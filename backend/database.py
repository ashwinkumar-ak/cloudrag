import logging

import psycopg

from backend.config import settings


logger = logging.getLogger(__name__)


def get_connection():
    return psycopg.connect(settings.database_url)


def check_database_connection() -> bool:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return True
    except psycopg.Error:
        logger.exception("Database health check failed")
        return False