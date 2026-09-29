from backend.embedding import EmbeddingService
from backend.repositories.chunks import ChunkRepository


def main():
    embedding_service = EmbeddingService()

    query = "How does CloudRAG store embeddings?"

    query_embedding = embedding_service.embed(query)

    results = ChunkRepository().search_chunks(
        query_embedding,
        limit=5,
    )

    for result in results:
        chunk_id, document_id, chunk_index, content, distance = result

        print(f"\nChunk ID: {chunk_id}")
        print(f"Document ID: {document_id}")
        print(f"Distance: {distance:.4f}")
        print(f"Content: {content}")


if __name__ == "__main__":
    main()