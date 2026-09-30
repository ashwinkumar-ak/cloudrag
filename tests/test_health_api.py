from fastapi.testclient import TestClient

from backend.main import app
from backend import main


client = TestClient(app)


def test_live_endpoint():
    response = client.get("/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_endpoint_when_dependencies_are_healthy(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_health_status",
        lambda: {
            "status": "ok",
            "dependencies": {
                "database": "ok",
                "ollama": "ok",
            },
        },
    )

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "cloudrag-api"
    assert data["status"] == "ok"
    assert data["dependencies"]["database"] == "ok"
    assert data["dependencies"]["ollama"] == "ok"

def test_ready_endpoint_when_dependencies_are_healthy(monkeypatch):
    monkeypatch.setattr(
        main,
        "is_ready",
        lambda: True,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_ready_endpoint_when_dependencies_are_unavailable(monkeypatch):
    monkeypatch.setattr(
        main,
        "is_ready",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Required dependencies are not ready",
    }