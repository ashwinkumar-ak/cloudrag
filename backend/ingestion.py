import time

from backend.chunking import TextChunker
from backend.embedding import EmbeddingService
from backend.metrics import (
    DOCUMENT_INGESTION_COUNT,
    DOCUMENT_INGESTION_LATENCY,
)
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository
from backend.repositories.spreadsheets import SpreadsheetRepository


class IngestionService:
    def __init__(self):
        self.document_repository = DocumentRepository()
        self.chunk_repository = ChunkRepository()
        self.embedding_service = EmbeddingService()
        self.spreadsheet_repository = SpreadsheetRepository()
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
        file_size: int | None = None,
        storage_path: str | None = None,
    ) -> int:
        if not text.strip():
            raise ValueError("Document text must not be empty")

        document_id = self.document_repository.create_document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=(
                file_size
                if file_size is not None
                else len(text.encode("utf-8"))
            ),
            storage_path=storage_path,
        )

        self.process_document(
            document_id=document_id,
            text=text,
        )
        return document_id

    def process_document(
        self,
        document_id: int,
        text: str,
        spreadsheet_rows: list[dict] | None = None,
    ) -> None:
        if not text.strip():
            raise ValueError("Document text must not be empty")

        start = time.perf_counter()

        self.document_repository.update_progress(
            document_id,
            status="processing",
            stage="parsing",
            progress=10,
            error_message=None,
        )

        try:
            self.document_repository.update_progress(
                document_id,
                status="processing",
                stage="chunking",
                progress=25,
                error_message=None,
            )

            chunks = self.chunker.split(text)

            if not chunks:
                raise ValueError("No usable text chunks were created.")

            self.chunk_repository.delete_document_chunks(document_id)
            self.spreadsheet_repository.delete_rows(document_id)

            if spreadsheet_rows:
                self.spreadsheet_repository.replace_rows(
                    document_id=document_id,
                    rows=spreadsheet_rows,
                )

            total_chunks = len(chunks)

            for index, chunk in enumerate(chunks):
                self.document_repository.update_progress(
                    document_id,
                    status="processing",
                    stage="embedding",
                    progress=25 + int(((index) / total_chunks) * 65),
                    error_message=None,
                )

                embedding = self.embedding_service.embed(chunk)

                self.chunk_repository.create_chunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )

            self.document_repository.update_progress(
                document_id,
                status="completed",
                stage="completed",
                progress=100,
                error_message=None,
            )

            DOCUMENT_INGESTION_COUNT.inc()

        except Exception as exc:
            message = str(exc).strip() or "Document processing failed."
            self.spreadsheet_repository.delete_rows(document_id)
            self.document_repository.update_progress(
                document_id,
                status="failed",
                stage="failed",
                progress=0,
                error_message=message[:1000],
            )
            raise

        finally:
            duration = time.perf_counter() - start
            DOCUMENT_INGESTION_LATENCY.observe(duration)
