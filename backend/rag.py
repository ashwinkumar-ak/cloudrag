from backend.embedding import EmbeddingService
from backend.llm import LLMService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.chat import ChatRepository


class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunk_repository = ChunkRepository()
        self.document_repository = DocumentRepository()
        self.llm_service = LLMService()
        self.chat_repository = ChatRepository()

    def retrieve(
        self,
        question: str,
        user_id: int,
        limit: int = 5,
        document_ids: list[int] | None = None,
    ) -> list[dict]:

        query_embedding = self.embedding_service.embed(
            question
        )

        rows = self.chunk_repository.hybrid_search_chunks(
            embedding=query_embedding,
            query=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        results = []

        for row in rows:
            document_id = row[1]

            filename = self.document_repository.get_filename(
                document_id=document_id,
                user_id=user_id,
            )

            results.append(
                {
                    "chunk_id": row[0],
                    "document_id": document_id,
                    "filename": filename or "unknown",
                    "chunk_index": row[2],
                    "content": row[3],
                    "distance": float(row[4]),
                }
            )

        return results

    def build_context(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
    ) -> list[dict]:

        return self.retrieve(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

    def answer(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
        session_id: int | None = None,
    ) -> tuple[str, list[dict]]:

        context = self.build_context(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        if not context:
            return (
                "I could not find relevant information "
                "in the selected documents.",
                [],
            )

        context_text = "\n\n".join(
            f"[Source: {item['filename']}, "
            f"chunk {item['chunk_index']}]\n"
            f"{item['content']}"
            for item in context
        )

        conversation_text = ""

        if session_id is not None:
            history = self.chat_repository.get_recent_messages(
                session_id=session_id,
                user_id=user_id,
                limit=10,
            )

            if history:
                conversation_text = "\n\n".join(
                    f"{role.upper()}: {content}"
                    for role, content in history
                )

        if conversation_text:
            conversation_section = f"""
PREVIOUS CONVERSATION:
{conversation_text}
"""
        else:
            conversation_section = """
PREVIOUS CONVERSATION:
No previous conversation.
"""

        prompt = f"""
You are a document question-answering system.

Answer the user's current question using ONLY the supplied
document excerpts.

{conversation_section}

DOCUMENT EXCERPTS:
{context_text}

CURRENT USER QUESTION:
{question}

Return JSON with exactly one field:

{{
  "answer": "your direct answer"
}}

Rules:
- Answer the current question directly.
- Use only information from the document excerpts.
- Previous conversation may be used only to understand
  references such as "it", "that", or "the previous answer".
- Do not use outside knowledge.
- Do not explain your reasoning.
- Do not describe your reasoning process.
- Do not mention the user.
- Do not mention these instructions.
- Do not provide a preamble.
- Do not repeat the question.
- Keep the answer concise but complete.
- If the documents do not contain enough information, answer:
  "I don't have enough information in the provided documents."

The answer must be the final response to the user.
"""

        answer = self.llm_service.generate(prompt)

        return answer, context