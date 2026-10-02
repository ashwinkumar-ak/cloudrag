from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """Dependency-free in-memory sliding-window rate limiter."""

    def __init__(self):
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._requests[key]

            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= limit:
                return False

            timestamps.append(now)
            return True

    def cleanup(self, max_keys: int = 5000) -> None:
        if len(self._requests) <= max_keys:
            return

        cutoff = time.monotonic() - 3600

        with self._lock:
            stale_keys = [
                key
                for key, timestamps in self._requests.items()
                if not timestamps or timestamps[-1] < cutoff
            ]

            for key in stale_keys:
                self._requests.pop(key, None)


rate_limiter = RateLimiter()

GENERAL_LIMIT = 120
GENERAL_WINDOW = 60

AUTH_LIMIT = 10
AUTH_WINDOW = 60

ASK_LIMIT = 10
ASK_WINDOW = 60

SEARCH_LIMIT = 30
SEARCH_WINDOW = 60
COMPARE_LIMIT = 10
COMPARE_WINDOW = 60
EVALUATION_LIMIT = 10
EVALUATION_WINDOW = 60

UPLOAD_LIMIT = 10
UPLOAD_WINDOW = 600


def get_client_identifier(request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    client = request.client

    if client and client.host:
        return client.host

    return "unknown"
