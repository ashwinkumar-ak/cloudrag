import psycopg

from backend.config import settings


class DocumentImageRepository:
    def replace_image(
        self,
        document_id: int,
        mime_type: str,
        storage_path: str,
        description: str,
        width: int | None = None,
        height: int | None = None,
    ) -> int:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO document_images
                        (document_id, mime_type, storage_path, width, height, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id)
                    DO UPDATE SET
                        mime_type = EXCLUDED.mime_type,
                        storage_path = EXCLUDED.storage_path,
                        width = EXCLUDED.width,
                        height = EXCLUDED.height,
                        description = EXCLUDED.description
                    RETURNING id
                    """,
                    (
                        document_id,
                        mime_type,
                        storage_path,
                        width,
                        height,
                        description,
                    ),
                )
                image_id = cursor.fetchone()[0]
            connection.commit()
        return image_id

    def delete_document_image(self, document_id: int) -> None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM document_images WHERE document_id = %s",
                    (document_id,),
                )
            connection.commit()

    def get_by_document(self, document_id: int):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, document_id, mime_type, storage_path,
                           width, height, description, created_at
                    FROM document_images
                    WHERE document_id = %s
                    """,
                    (document_id,),
                )
                return cursor.fetchone()
