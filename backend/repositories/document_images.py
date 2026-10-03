import psycopg

from backend.config import settings


class DocumentImageRepository:
    def replace_images(self, document_id: int, images: list[dict]) -> list[int]:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM document_images WHERE document_id = %s",
                    (document_id,),
                )
                ids = []
                for image in images:
                    cursor.execute(
                        """
                        INSERT INTO document_images
                            (document_id, mime_type, storage_path, width, height, description,
                             source_label, image_index)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            document_id,
                            image["mime_type"],
                            image["storage_path"],
                            image.get("width"),
                            image.get("height"),
                            image["description"],
                            image.get("source_label"),
                            image.get("image_index", 0),
                        ),
                    )
                    ids.append(cursor.fetchone()[0])
            connection.commit()
        return ids

    def replace_image(self, document_id: int, mime_type: str, storage_path: str,
                      description: str, width: int | None = None,
                      height: int | None = None) -> int:
        return self.replace_images(document_id, [{
            "mime_type": mime_type,
            "storage_path": storage_path,
            "description": description,
            "width": width,
            "height": height,
            "source_label": "Standalone image",
            "image_index": 0,
        }])[0]

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
                           width, height, description, created_at,
                           source_label, image_index
                    FROM document_images
                    WHERE document_id = %s
                    ORDER BY image_index, id
                    LIMIT 1
                    """,
                    (document_id,),
                )
                return cursor.fetchone()

    def list_by_document(self, document_id: int, limit: int = 3):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, document_id, mime_type, storage_path,
                           width, height, description, created_at,
                           source_label, image_index
                    FROM document_images
                    WHERE document_id = %s
                    ORDER BY image_index, id
                    LIMIT %s
                    """,
                    (document_id, limit),
                )
                return cursor.fetchall()
