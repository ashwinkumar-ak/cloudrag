import time

from backend.chunking import TextChunker
from backend.embedding import EmbeddingService
from backend.metrics import (
    DOCUMENT_INGESTION_COUNT,
    DOCUMENT_INGESTION_LATENCY,
)
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository


class IngestionService:
    def __init__(self):
        self.document_repository = DocumentRepository()
        self.chunk_repository = ChunkRepository()
        self.embedding_service = EmbeddingService()
        self.chunker = TextChunker(
            chunk_size=1000,
            overlap_sentences=1,
        )

    def ingest_text(
        self,
        user_id: int,
        filename: str,
        content_type: str,
        text: str,
    ) -> int:
        if not text.strip():
            raise ValueError("Document text must not be empty")

        start = time.perf_counter()

        document_id = self.document_repository.create_document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=len(text.encode("utf-8")),
        )

        self.document_repository.update_status(
            document_id,
            "processing",
        )

        try:
            chunks = self.chunker.split(text)

            for index, chunk in enumerate(chunks):
                embedding = self.embedding_service.embed(chunk)

                self.chunk_repository.create_chunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )

            self.document_repository.update_status(
                document_id,
                "completed",
            )

            DOCUMENT_INGESTION_COUNT.inc()

            return document_id

        except Exception:
            self.document_repository.update_status(
                document_id,
                "failed",
            )
            raise

        finally:
            duration = time.perf_counter() - start
            DOCUMENT_INGESTION_LATENCY.observe(duration)