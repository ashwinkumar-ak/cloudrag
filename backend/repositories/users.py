import psycopg

from backend.config import settings


class UserRepository:

    def create_user(
        self,
        email: str,
        password_hash: str,
    ) -> int:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (
                        email,
                        password_hash
                    )
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (
                        email,
                        password_hash,
                    ),
                )

                user_id = cursor.fetchone()[0]

            connection.commit()

        return user_id

    def get_by_email(
        self,
        email: str,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        email,
                        password_hash,
                        created_at,
                        updated_at
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )

                return cursor.fetchone()

    def get_by_id(
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
                        email,
                        password_hash,
                        created_at,
                        updated_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )

                return cursor.fetchone()