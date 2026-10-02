from fastapi.testclient import TestClient

from backend.main import app
from backend.security import RateLimiter


client = TestClient(app)


def test_rate_limiter_enforces_sliding_window():
    limiter = RateLimiter()

    assert limiter.allow("client", 2, 60) is True
    assert limiter.allow("client", 2, 60) is True
    assert limiter.allow("client", 2, 60) is False


def test_security_headers_are_present():
    response = client.get("/live")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers["Permissions-Policy"]


def test_oversized_upload_is_rejected_before_upload_processing(monkeypatch):
    from backend import main

    monkeypatch.setattr(
        main.settings,
        "max_upload_size_bytes",
        10,
    )

    response = client.post(
        "/documents",
        headers={
            "Authorization": "Bearer invalid",
            "Content-Length": "2000000",
        },
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()
