import psycopg

from backend.config import settings
from backend.embedding import EmbeddingService


def main():
    embedding_service = EmbeddingService()

    text = "CloudRAG stores document chunks for semantic search."
    embedding = embedding_service.embed(text)

    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chunks (
                    document_id,
                    chunk_index,
                    content,
                    embedding
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (1, 1, text, embedding),
            )

            chunk_id = cursor.fetchone()[0]

    print(f"Inserted chunk: {chunk_id}")
    print(f"Embedding dimensions: {len(embedding)}")


if __name__ == "__main__":
    main()