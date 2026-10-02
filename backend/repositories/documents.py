import psycopg

from backend.config import settings


class DocumentRepository:

    def create_document(
        self,
        user_id: int,
        filename: str,
        content_type: str,
        file_size: int,
        storage_path: str | None = None,
    ) -> int:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        user_id,
                        filename,
                        content_type,
                        file_size,
                        status,
                        storage_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        filename,
                        content_type,
                        file_size,
                        "pending",
                        storage_path,
                    ),
                )

                document_id = cursor.fetchone()[0]

            connection.commit()

        return document_id

    def update_status(
        self,
        document_id: int,
        status: str,
    ) -> None:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE documents
                    SET
                        status = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        status,
                        document_id,
                    ),
                )

            connection.commit()

    def get_filename(
        self,
        document_id: int,
        user_id: int,
    ) -> str | None:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT filename
                    FROM documents
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        document_id,
                        user_id,
                    ),
                )

                row = cursor.fetchone()

        return row[0] if row else None

    def get_storage_path(
        self,
        document_id: int,
        user_id: int,
    ) -> str | None:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT storage_path
                    FROM documents
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        document_id,
                        user_id,
                    ),
                )

                row = cursor.fetchone()

        return row[0] if row else None

    def get_document(
        self,
        document_id: int,
        user_id: int,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:

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
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        document_id,
                        user_id,
                    ),
                )

                return cursor.fetchone()

    def list_documents(
        self,
        user_id: int,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:

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
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )

                return cursor.fetchall()

    def delete_document(
        self,
        document_id: int,
        user_id: int,
    ) -> bool:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM documents
                    WHERE id = %s
                    AND user_id = %s
                    RETURNING id
                    """,
                    (
                        document_id,
                        user_id,
                    ),
                )

                deleted = cursor.fetchone()

            connection.commit()

        return deleted is not None