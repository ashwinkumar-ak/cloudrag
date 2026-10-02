import json

import psycopg

from backend.config import settings


class SpreadsheetRepository:
    def replace_rows(self, document_id: int, rows: list[dict]) -> None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM spreadsheet_rows WHERE document_id = %s",
                    (document_id,),
                )
                for row in rows:
                    cursor.execute(
                        """
                        INSERT INTO spreadsheet_rows (
                            document_id, sheet_name, row_number,
                            data, display_data
                        )
                        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
                        """,
                        (
                            document_id,
                            row["sheet_name"],
                            row["row_number"],
                            json.dumps(row["data"]),
                            json.dumps(row["display_data"]),
                        ),
                    )
            connection.commit()

    def delete_rows(self, document_id: int) -> None:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM spreadsheet_rows WHERE document_id = %s",
                    (document_id,),
                )
            connection.commit()

    def get_rows(
        self,
        user_id: int,
        document_ids: list[int] | None = None,
    ) -> list[dict]:
        with psycopg.connect(settings.database_url) as connection:
            with connection.cursor() as cursor:
                if document_ids:
                    cursor.execute(
                        """
                        SELECT r.id, r.document_id, d.filename,
                               r.sheet_name, r.row_number,
                               r.data, r.display_data
                        FROM spreadsheet_rows r
                        INNER JOIN documents d ON d.id = r.document_id
                        WHERE d.user_id = %s
                          AND r.document_id = ANY(%s)
                          AND d.status = 'completed'
                        ORDER BY r.document_id, r.sheet_name, r.row_number
                        """,
                        (user_id, document_ids),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT r.id, r.document_id, d.filename,
                               r.sheet_name, r.row_number,
                               r.data, r.display_data
                        FROM spreadsheet_rows r
                        INNER JOIN documents d ON d.id = r.document_id
                        WHERE d.user_id = %s
                          AND d.status = 'completed'
                        ORDER BY r.document_id, r.sheet_name, r.row_number
                        """,
                        (user_id,),
                    )
                return [
                    {
                        "id": row[0],
                        "document_id": row[1],
                        "filename": row[2],
                        "sheet_name": row[3],
                        "row_number": row[4],
                        "data": row[5] or {},
                        "display_data": row[6] or {},
                    }
                    for row in cursor.fetchall()
                ]
