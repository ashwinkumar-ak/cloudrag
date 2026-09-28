import psycopg

from backend.config import settings


def main():
    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()

            print(result[0])


if __name__ == "__main__":
    main()