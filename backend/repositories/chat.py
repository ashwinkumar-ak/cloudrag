import psycopg

from backend.config import settings


class ChatRepository:
    def create_session(
        self,
        title: str = "New Chat",
    ) -> int:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_sessions (
                        title
                    )
                    VALUES (%s)
                    RETURNING id
                    """,
                    (title,),
                )

                session_id = cursor.fetchone()[0]

            connection.commit()

        return session_id

    def list_sessions(self):
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        created_at,
                        updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                    """
                )

                return cursor.fetchall()

    def get_session(
        self,
        session_id: int,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        created_at,
                        updated_at
                    FROM chat_sessions
                    WHERE id = %s
                    """,
                    (session_id,),
                )

                return cursor.fetchone()

    def delete_session(
        self,
        session_id: int,
    ) -> bool:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM chat_sessions
                    WHERE id = %s
                    RETURNING id
                    """,
                    (session_id,),
                )

                deleted = cursor.fetchone()

            connection.commit()

        return deleted is not None

    def update_title(
        self,
        session_id: int,
        title: str,
    ) -> None:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET
                        title = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        title,
                        session_id,
                    ),
                )

            connection.commit()

    def touch_session(
        self,
        session_id: int,
    ) -> None:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = NOW()
                    WHERE id = %s
                    """,
                    (session_id,),
                )

            connection.commit()

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
    ) -> int:
        if role not in {"user", "assistant"}:
            raise ValueError(
                "Message role must be 'user' or 'assistant'."
            )

        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages (
                        session_id,
                        role,
                        content
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        session_id,
                        role,
                        content,
                    ),
                )

                message_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = NOW()
                    WHERE id = %s
                    """,
                    (session_id,),
                )

            connection.commit()

        return message_id

    def get_messages(
        self,
        session_id: int,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        session_id,
                        role,
                        content,
                        created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC, id ASC
                    """,
                    (session_id,),
                )

                return cursor.fetchall()

    def get_recent_messages(
        self,
        session_id: int,
        limit: int = 10,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        role,
                        content
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (
                        session_id,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

        rows.reverse()

        return rows

    def update_title(
        self,
        session_id: int,
        title: str,
    ) -> None:
        with psycopg.connect(
            settings.database_url
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET
                        title = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        title,
                        session_id,
                    ),
                )
    
            connection.commit()