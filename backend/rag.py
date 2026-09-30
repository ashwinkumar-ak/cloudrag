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

    def retrieve(self, question: str, limit: int = 5) -> list[dict]:
        query_embedding = self.embedding_service.embed(question)

        rows = self.chunk_repository.search_chunks(
            embedding=query_embedding,
            limit=limit,
        )

        results = []

        for row in rows:
            document_id = row[1]
            filename = self.document_repository.get_filename(document_id)

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

    def build_context(self, question: str, limit: int = 3) -> list[dict]:
        return self.retrieve(question, limit)

    def answer(self, question: str, limit: int = 3) -> tuple[str, list[dict]]:
        context = self.build_context(question, limit)

        if not context:
            return "I could not find relevant information.", []

        context_text = "\n\n".join(
            (
                f"Source: {item['filename']}, "
                f"chunk {item['chunk_index']}\n"
                f"{item['content']}"
            )
            for item in context
        )

        prompt = f"""
        Answer the question using only the context below.
        
        Rules:
        - Do not use outside knowledge.
        - Do not invent facts.
        - Keep the answer short.
        - If the context does not answer the question, say:
        I don't have enough information in the provided documents.
        - Cite supporting sources as [Source: filename, chunk N].
        
        Context:
        {context_text}
        
        Question:
        {question}
        
        Answer:
        """.strip()

        answer = self.llm_service.generate(prompt)

        return answer, context