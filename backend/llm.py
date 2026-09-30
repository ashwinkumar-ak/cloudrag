import json
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
                        "format": {
                            "type": "object",
                            "properties": {
                                "answer": {
                                    "type": "string"
                                }
                            },
                            "required": ["answer"],
                        },
                        "options": {
                            "temperature": 0,
                            "num_predict": 180,
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
                data = response.json()
            except ValueError as exc:
                raise LLMGenerationError(
                    "The language model returned an invalid response."
                ) from exc

            raw_response = data.get("response")

            if not isinstance(raw_response, str):
                raise LLMGenerationError(
                    "The language model returned an invalid response."
                )

            answer = self._parse_answer(raw_response)

            if not answer:
                raise LLMGenerationError(
                    "The language model returned an empty answer."
                )

            return answer

        finally:
            duration = time.perf_counter() - start
            LLM_LATENCY.observe(duration)

    def _parse_answer(self, raw_response: str) -> str:
        raw_response = raw_response.strip()

        try:
            parsed = json.loads(raw_response)

            if isinstance(parsed, dict):
                answer = parsed.get("answer")

                if isinstance(answer, str):
                    return answer.strip()

        except json.JSONDecodeError:
            pass

        # Fallback in case the local Ollama version/model does
        # not perfectly follow the JSON schema.
        return raw_response