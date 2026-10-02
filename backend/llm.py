import json
import time

import requests

from backend.config import settings
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
        self.base_url = base_url or settings.ollama_base_url

    def generate(self, prompt: str, max_output_tokens: int = 180) -> str:
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
                            "properties": {"answer": {"type": "string"}},
                            "required": ["answer"],
                        },
                        "options": {
                            "temperature": 0,
                            "num_predict": max_output_tokens,
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

    def generate_stream(self, prompt: str, max_output_tokens: int = 180):
        """Yield plain-text Ollama response chunks as they arrive."""
        start = time.perf_counter()
        response = None

        try:
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True,
                        "think": False,
                        "options": {
                            "temperature": 0,
                            "num_predict": max_output_tokens,
                        },
                    },
                    timeout=300,
                    stream=True,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                raise LLMGenerationError(
                    "The local language model could not generate a streamed response."
                ) from exc

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                try:
                    data = json.loads(raw_line)
                except (TypeError, json.JSONDecodeError):
                    continue

                text = data.get("response")
                if isinstance(text, str) and text:
                    yield text

                if data.get("done"):
                    break
        except LLMGenerationError:
            raise
        except requests.RequestException as exc:
            raise LLMGenerationError(
                "The local language model could not complete the streamed response."
            ) from exc
        finally:
            if response is not None:
                response.close()
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

        return raw_response
