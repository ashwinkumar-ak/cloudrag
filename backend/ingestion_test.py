from backend.ingestion import IngestionService
from backend.repositories.documents import DocumentRepository


def main():
    service = IngestionService()

    document_id = service.ingest_text(
        filename="cloudrag-introduction.txt",
        content_type="text/plain",
        text=(
            "CloudRAG is a document intelligence platform. "
            "It processes documents and creates embeddings. "
            "The embeddings are stored in PostgreSQL using pgvector. "
            "Users can search documents using semantic similarity."
        ),
    )

    print(f"Ingested document: {document_id}")

    document = DocumentRepository().get_document(document_id)

    print(f"Document: {document}")


if __name__ == "__main__":
    main()