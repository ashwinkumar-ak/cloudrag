from backend.database import check_database_connection


def get_health_status():
    database_healthy = check_database_connection()

    return {
        "status": "ok" if database_healthy else "degraded",
        "dependencies": {
            "database": "ok" if database_healthy else "unavailable",
        },
    }


def is_ready() -> bool:
    return check_database_connection()