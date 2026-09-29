from backend.embedding import EmbeddingService
from backend.repositories.chunks import ChunkRepository
from backend.repositories.documents import DocumentRepository


def main():
    document_repository = DocumentRepository()
    chunk_repository = ChunkRepository()
    embedding_service = EmbeddingService()

    document_id = document_repository.create_document(
        filename="chunk-test.txt",
        content_type="text/plain",
        file_size=256,
    )

    content = "CloudRAG uses vector embeddings for semantic document retrieval."
    embedding = embedding_service.embed(content)

    chunk_id = chunk_repository.create_chunk(
        document_id=document_id,
        chunk_index=0,
        content=content,
        embedding=embedding,
    )

    print(f"Document: {document_id}")
    print(f"Chunk: {chunk_id}")
    print(f"Embedding dimensions: {len(embedding)}")


if __name__ == "__main__":
    main()