import psycopg

from backend.config import settings
from backend.models import Document


class DocumentRepository:
    def create_document(
        self,
        filename: str,
        content_type: str,
        file_size: int,
    ) -> int:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        filename,
                        content_type,
                        file_size
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (filename, content_type, file_size),
                )

                document_id = cursor.fetchone()[0]

            connection.commit()

        return document_id

    def get_document(self, document_id: int):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        filename,
                        content_type,
                        file_size,
                        status,
                        created_at,
                        updated_at
                    FROM documents
                    WHERE id = %s;
                    """,
                    (document_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                return Document(
                    id=row[0],
                    filename=row[1],
                    content_type=row[2],
                    file_size=row[3],
                    status=row[4],
                    created_at=row[5],
                    updated_at=row[6],
                )
            
    def update_status(self, document_id: int, status: str) -> None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE documents
                    SET status = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (status, document_id),
                )
    
            connection.commit()

    def get_filename(self, document_id: int) -> str | None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT filename
                    FROM documents
                    WHERE id = %s;
                    """,
                    (document_id,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                return row[0]