import time

import requests

from backend.config import settings
from backend.metrics import EMBEDDING_LATENCY


class EmbeddingService:
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        self.model_name = (
            model_name or settings.gemini_embedding_model
        )
        self.api_key = api_key or settings.gemini_api_key
        self.base_url = settings.gemini_api_base_url
        self.dimension = 768

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text must not be empty")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        start = time.perf_counter()
        response = None

        try:
            response = requests.post(
                f"{self.base_url}/models/"
                f"{self.model_name}:embedContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json={
                    "content": {
                        "parts": [
                            {"text": text}
                        ]
                    },
                    "output_dimensionality": self.dimension,
                },
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            embedding = (
                data.get("embedding", {})
                .get("values")
            )

            if not isinstance(embedding, list):
                raise RuntimeError(
                    "Gemini returned an invalid embedding response."
                )

            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Expected {self.dimension} dimensions, "
                    f"got {len(embedding)}"
                )

            return embedding

        except requests.RequestException as exc:
            if response is not None:
                detail = response.text[:2000]
                raise RuntimeError(
                    f"Gemini embedding request failed "
                    f"(HTTP {response.status_code}): {detail}"
                ) from exc

            raise RuntimeError(
                "Gemini embedding service could not generate "
                "an embedding."
            ) from exc

        finally:
            duration = time.perf_counter() - start
            EMBEDDING_LATENCY.observe(duration)