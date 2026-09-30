import psycopg

from backend.config import settings


class ChatRepository:

    def create_session(
        self,
        user_id: int,
        title: str = "New Chat",
    ) -> int:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_sessions (
                        user_id,
                        title
                    )
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        title,
                    ),
                )

                session_id = cursor.fetchone()[0]

            connection.commit()

        return session_id

    def list_sessions(
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
                        title,
                        created_at,
                        updated_at
                    FROM chat_sessions
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                )

                return cursor.fetchall()

    def get_session(
        self,
        session_id: int,
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
                        title,
                        created_at,
                        updated_at
                    FROM chat_sessions
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        session_id,
                        user_id,
                    ),
                )

                return cursor.fetchone()

    def delete_session(
        self,
        session_id: int,
        user_id: int,
    ) -> bool:
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM chat_sessions
                    WHERE id = %s
                    AND user_id = %s
                    RETURNING id
                    """,
                    (
                        session_id,
                        user_id,
                    ),
                )

                deleted = cursor.fetchone()

            connection.commit()

        return deleted is not None

    def update_title(
        self,
        session_id: int,
        user_id: int,
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
                    AND user_id = %s
                    """,
                    (
                        title,
                        session_id,
                        user_id,
                    ),
                )

            connection.commit()

    def touch_session(
        self,
        session_id: int,
        user_id: int,
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
                    AND user_id = %s
                    """,
                    (
                        session_id,
                        user_id,
                    ),
                )

            connection.commit()

    def add_message(
        self,
        session_id: int,
        user_id: int,
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
                    SELECT
                        %s,
                        %s,
                        %s
                    WHERE EXISTS (
                        SELECT 1
                        FROM chat_sessions
                        WHERE id = %s
                        AND user_id = %s
                    )
                    RETURNING id
                    """,
                    (
                        session_id,
                        role,
                        content,
                        session_id,
                        user_id,
                    ),
                )

                row = cursor.fetchone()

                if row is None:
                    connection.rollback()
                    raise ValueError(
                        "Session not found."
                    )

                message_id = row[0]

                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET updated_at = NOW()
                    WHERE id = %s
                    AND user_id = %s
                    """,
                    (
                        session_id,
                        user_id,
                    ),
                )

            connection.commit()

        return message_id

    def get_messages(
        self,
        session_id: int,
        user_id: int,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        m.id,
                        m.session_id,
                        m.role,
                        m.content,
                        m.created_at
                    FROM chat_messages m
                    INNER JOIN chat_sessions s
                        ON s.id = m.session_id
                    WHERE m.session_id = %s
                    AND s.user_id = %s
                    ORDER BY
                        m.created_at ASC,
                        m.id ASC
                    """,
                    (
                        session_id,
                        user_id,
                    ),
                )

                return cursor.fetchall()

    def get_recent_messages(
        self,
        session_id: int,
        user_id: int,
        limit: int = 10,
    ):
        with psycopg.connect(
            settings.database_url
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        m.role,
                        m.content
                    FROM chat_messages m
                    INNER JOIN chat_sessions s
                        ON s.id = m.session_id
                    WHERE m.session_id = %s
                    AND s.user_id = %s
                    ORDER BY
                        m.created_at DESC,
                        m.id DESC
                    LIMIT %s
                    """,
                    (
                        session_id,
                        user_id,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

        rows.reverse()

        return rows