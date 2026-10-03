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
                             source_label, image_index, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
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
                            image.get("embedding"),
                        ),
                    )
                    ids.append(cursor.fetchone()[0])
            connection.commit()
        return ids

    def replace_image(self, document_id: int, mime_type: str, storage_path: str,
                      description: str, width: int | None = None,
                      height: int | None = None,
                      embedding: list[float] | None = None) -> int:
        return self.replace_images(document_id, [{
            "mime_type": mime_type,
            "storage_path": storage_path,
            "description": description,
            "width": width,
            "height": height,
            "source_label": "Standalone image",
            "image_index": 0,
            "embedding": embedding,
        }])[0]


    def search_images(
        self,
        embedding: list[float],
        user_id: int,
        limit: int = 10,
        distance_threshold: float | None = None,
        document_ids: list[int] | None = None,
    ):
        if distance_threshold is None:
            distance_threshold = settings.multimodal_retrieval_distance_threshold

        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                document_filter = ""
                parameters = [embedding, user_id, embedding, distance_threshold]
                if document_ids:
                    document_filter = " AND di.document_id = ANY(%s)"
                    parameters.append(document_ids)
                parameters.extend([embedding, limit])
                cursor.execute(
                    f"""
                    SELECT
                        di.id,
                        di.document_id,
                        di.mime_type,
                        di.storage_path,
                        di.width,
                        di.height,
                        di.description,
                        di.created_at,
                        di.source_label,
                        di.image_index,
                        di.embedding <=> %s::vector AS distance
                    FROM document_images di
                    INNER JOIN documents d ON d.id = di.document_id
                    WHERE d.user_id = %s
                      AND di.embedding IS NOT NULL
                      AND di.embedding <=> %s::vector <= %s
                      {document_filter}
                    ORDER BY di.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    tuple(parameters),
                )
                return cursor.fetchall()

    def list_for_user(self, user_id: int, document_ids: list[int] | None = None):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                document_filter = ""
                parameters = [user_id]
                if document_ids:
                    document_filter = " AND di.document_id = ANY(%s)"
                    parameters.append(document_ids)
                cursor.execute(
                    f"""
                    SELECT di.id, di.document_id, di.mime_type, di.storage_path,
                           di.width, di.height, di.description, di.created_at,
                           di.source_label, di.image_index, di.embedding
                    FROM document_images di
                    JOIN documents d ON d.id = di.document_id
                    WHERE d.user_id = %s {document_filter}
                    ORDER BY di.document_id, di.image_index, di.id
                    """,
                    tuple(parameters),
                )
                return cursor.fetchall()

    def update_embedding(self, image_id: int, embedding: list[float]) -> None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE document_images SET embedding = %s::vector WHERE id = %s",
                    (embedding, image_id),
                )
            connection.commit()

    def get_by_id_for_user(self, image_id: int, user_id: int):
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT di.id, di.document_id, di.mime_type, di.storage_path,
                           di.width, di.height, di.description, di.created_at,
                           di.source_label, di.image_index
                    FROM document_images di
                    JOIN documents d ON d.id = di.document_id
                    WHERE di.id = %s AND d.user_id = %s
                    """,
                    (image_id, user_id),
                )
                return cursor.fetchone()

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
