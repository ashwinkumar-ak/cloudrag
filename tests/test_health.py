from backend import health


def test_health_status_when_dependencies_are_healthy(monkeypatch):
    monkeypatch.setattr(
        health,
        "check_database_connection",
        lambda: True,
    )
    monkeypatch.setattr(
        health,
        "check_ollama_connection",
        lambda: True,
    )

    result = health.get_health_status()

    assert result["status"] == "ok"
    assert result["dependencies"]["database"] == "ok"
    assert result["dependencies"]["ollama"] == "ok"


def test_health_status_when_ollama_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        health,
        "check_database_connection",
        lambda: True,
    )
    monkeypatch.setattr(
        health,
        "check_ollama_connection",
        lambda: False,
    )

    result = health.get_health_status()

    assert result["status"] == "degraded"
    assert result["dependencies"]["database"] == "ok"
    assert result["dependencies"]["ollama"] == "unavailable"