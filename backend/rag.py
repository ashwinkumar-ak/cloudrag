from backend.embedding import EmbeddingService
from backend.llm import LLMService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.chat import ChatRepository
from backend.spreadsheet_query import SpreadsheetQueryService
from backend.repositories.document_images import DocumentImageRepository
from backend.storage import DocumentStorage


class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunk_repository = ChunkRepository()
        self.document_repository = DocumentRepository()
        self.llm_service = LLMService()
        self.chat_repository = ChatRepository()
        self.spreadsheet_query_service = SpreadsheetQueryService()
        self.document_image_repository = DocumentImageRepository()
        self.document_storage = DocumentStorage()

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

            image_row = self.document_image_repository.get_by_document(document_id)
            results.append(
                {
                    "chunk_id": row[0],
                    "document_id": document_id,
                    "filename": filename or "unknown",
                    "chunk_index": row[2],
                    "content": row[3],
                    "distance": float(row[4]),
                    "image": bool(image_row),
                    "image_mime_type": image_row[2] if image_row else None,
                    "image_storage_path": image_row[3] if image_row else None,
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

    def answer_stream(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
        session_id: int | None = None,
        model: str | None = None,
    ) -> tuple[list[dict], object]:
        """Prepare RAG context and return an answer chunk iterator."""

        if self.spreadsheet_query_service.is_spreadsheet_query(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
        ):
            answer, context = self.spreadsheet_query_service.answer(
                question=question,
                user_id=user_id,
                document_ids=document_ids,
            )
            return context, iter([answer])

        context = self.build_context(
            question=question,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids,
        )

        if not context:
            return [], iter([
                "I could not find relevant information "
                "in the selected documents."
            ])

        image_inputs = []
        context_sections = []
        for item in context:
            context_sections.append(
                f"[Source: {item['filename']}, chunk {item['chunk_index']}]\n"
                f"{item['content']}"
            )
            if item.get("image") and len(image_inputs) < 1:
                try:
                    image_bytes = self.document_storage.download(item["image_storage_path"])
                    image_inputs.append({
                        "mime_type": item["image_mime_type"],
                        "bytes": image_bytes,
                    })
                except Exception:
                    pass

        context_text = "\n\n".join(context_sections)

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
- When image input is provided, use the visual evidence together with the retrieved description.

Return ONLY the final answer as plain text.
"""

        llm_service = LLMService(model=model)
        return context, llm_service.generate_stream(prompt, image_inputs=image_inputs)

    def answer(
        self,
        question: str,
        user_id: int,
        limit: int = 3,
        document_ids: list[int] | None = None,
        session_id: int | None = None,
        model: str | None = None,
    ) -> tuple[str, list[dict]]:

        if self.spreadsheet_query_service.is_spreadsheet_query(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
        ):
            return self.spreadsheet_query_service.answer(
                question=question,
                user_id=user_id,
                document_ids=document_ids,
            )

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

        image_inputs = []
        context_sections = []
        for item in context:
            context_sections.append(
                f"[Source: {item['filename']}, chunk {item['chunk_index']}]\n"
                f"{item['content']}"
            )
            if item.get("image") and len(image_inputs) < 1:
                try:
                    image_bytes = self.document_storage.download(item["image_storage_path"])
                    image_inputs.append({
                        "mime_type": item["image_mime_type"],
                        "bytes": image_bytes,
                    })
                except Exception:
                    pass

        context_text = "\n\n".join(context_sections)

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
- When image input is provided, use the visual evidence together with the retrieved description.

The answer must be the final response to the user.
"""

        llm_service = LLMService(model=model)
        answer = llm_service.generate(prompt, image_inputs=image_inputs)

        return answer, context