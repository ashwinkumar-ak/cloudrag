from backend.embedding import EmbeddingService
from backend.llm import LLMService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository


class RAGService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunk_repository = ChunkRepository()
        self.document_repository = DocumentRepository()
        self.llm_service = LLMService()

    def retrieve(self, question: str, limit: int = 5):
        query_embedding = self.embedding_service.embed(question)

        rows = self.chunk_repository.search_chunks(
            embedding=query_embedding,
            limit=limit,
        )

        return rows

    def build_context(self, question: str, limit: int = 5) -> list[dict]:
        rows = self.retrieve(question, limit)

        context = []

        for row in rows:
            document_id = row[1]
            filename = self.document_repository.get_filename(document_id)

            context.append(
                {
                    "chunk_id": row[0],
                    "document_id": document_id,
                    "filename": filename or "unknown",
                    "chunk_index": row[2],
                    "content": row[3],
                    "distance": float(row[4]),
                }
            )

        return context

    def answer(self, question: str, limit: int = 5) -> tuple[str, list[dict]]:
        context = self.build_context(question, limit)

        if not context:
            return "I could not find relevant information.", []

        context_text = "\n\n".join(
            f"[Source: {item['filename']}, chunk {item['chunk_index']}]\n"
            f"{item['content']}"
            for item in context
        )

        prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided context.

If the context does not contain enough information to answer the question,
say that you do not have enough information.

Always cite the source IDs you used, for example [Source 12].

Context:
{context_text}

Question:
{question}

Answer:
""".strip()

        answer = self.llm_service.generate(prompt)

        return answer, context