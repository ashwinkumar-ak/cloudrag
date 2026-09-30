import os
import requests

from backend.database import check_database_connection


def check_ollama_connection() -> bool:
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    )

    try:
        response = requests.get(
            f"{base_url}/api/tags",
            timeout=3,
        )
        return response.ok

    except requests.RequestException:
        return False


def get_health_status():
    database_healthy = check_database_connection()
    ollama_healthy = check_ollama_connection()

    return {
        "status": "ok" if database_healthy and ollama_healthy else "degraded",
        "dependencies": {
            "database": "ok" if database_healthy else "unavailable",
            "ollama": "ok" if ollama_healthy else "unavailable",
        },
    }


def is_ready() -> bool:
    return check_database_connection() and check_ollama_connection()