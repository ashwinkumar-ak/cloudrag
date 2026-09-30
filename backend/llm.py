import os
import time

import requests

from backend.metrics import LLM_LATENCY


class LLMGenerationError(RuntimeError):
    """Raised when the configured LLM cannot generate an answer."""


class LLMService:
    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str | None = None,
    ):
        self.model = model
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        )

    def generate(self, prompt: str) -> str:
        start = time.perf_counter()

        try:
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "think": False,
                        "options": {
                            "temperature": 0,
                            "num_predict": 150,
                        },
                    },
                    timeout=300,
                )

                response.raise_for_status()

            except requests.RequestException as exc:
                raise LLMGenerationError(
                    "The local language model could not generate a response."
                ) from exc

            try:
                answer = response.json()["response"]
            except (ValueError, KeyError, TypeError) as exc:
                raise LLMGenerationError(
                    "The language model returned an invalid response."
                ) from exc

            return self._clean_answer(answer)

        finally:
            duration = time.perf_counter() - start
            LLM_LATENCY.observe(duration)

    def _clean_answer(self, answer: str) -> str:
        if "</think>" in answer:
            answer = answer.split("</think>", 1)[1]

        return answer.strip()