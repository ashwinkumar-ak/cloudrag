import psycopg

from backend.config import settings


class ChunkRepository:
    def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: list[float],
    ) -> int:
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
                    VALUES (%s, %s, %s, %s::vector)
                    RETURNING id;
                    """,
                    (document_id, chunk_index, content, embedding),
                )

                chunk_id = cursor.fetchone()[0]

            connection.commit()

        return chunk_id

    def search_chunks(
        self,
        embedding: list[float],
        limit: int = 5,
    ):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        document_id,
                        chunk_index,
                        content,
                        embedding <=> %s::vector AS distance
                    FROM chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (embedding, embedding, limit),
                )
    
                return cursor.fetchall()