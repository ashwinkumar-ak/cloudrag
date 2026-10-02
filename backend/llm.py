import json
import time

import requests

from backend.config import settings
from backend.metrics import LLM_LATENCY
from backend.model_registry import validate_model


class LLMGenerationError(RuntimeError):
    """Raised when the configured LLM cannot generate an answer."""


class LLMService:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ):
        self.model = validate_model(model or settings.gemini_model)
        self.api_key = api_key or settings.gemini_api_key

        self.base_url = settings.gemini_api_base_url

    def generate(self, prompt: str, max_output_tokens: int = 180) -> str:
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )
        start = time.perf_counter()

        try:
            try:
                response = requests.post(
                    f"{self.base_url}/models/"
                    f"{self.model}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0,
                            "maxOutputTokens": max_output_tokens,
                            "responseMimeType": (
                                "application/json"
                            ),
                            "responseSchema": {
                                "type": "OBJECT",
                                "properties": {
                                    "answer": {
                                        "type": "STRING"
                                    }
                                },
                                "required": ["answer"],
                            },
                        },
                    },
                    timeout=120,
                )

                response.raise_for_status()

            except requests.RequestException as exc:
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    status_code = exc.response.status_code
                    try:
                        error_data = exc.response.json()
                        error_message = (
                            error_data.get("error", {}).get("message")
                            or "Unknown Gemini API error."
                        )
                    except ValueError:
                        error_message = "Unknown Gemini API error."
            
                    raise LLMGenerationError(
                        f"Gemini API error ({status_code}): "
                        f"{error_message}"
                    ) from exc
            
                raise LLMGenerationError(
                    "The cloud language model could not "
                    "generate a response."
                ) from exc
            try:
                data = response.json()
            except ValueError as exc:
                raise LLMGenerationError(
                    "The language model returned an "
                    "invalid response."
                ) from exc

            candidates = data.get("candidates")

            if not isinstance(candidates, list) or not candidates:
                raise LLMGenerationError(
                    "The language model returned no candidates."
                )

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            if not isinstance(parts, list) or not parts:
                raise LLMGenerationError(
                    "The language model returned no content."
                )

            raw_response = parts[0].get("text")

            if not isinstance(raw_response, str):
                raise LLMGenerationError(
                    "The language model returned invalid content."
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


    def generate_stream(self, prompt: str):
        """Yield plain-text Gemini response chunks as they arrive."""
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        start = time.perf_counter()
        response = None

        try:
            try:
                response = requests.post(
                    f"{self.base_url}/models/"
                    f"{self.model}:streamGenerateContent?alt=sse",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0,
                            "maxOutputTokens": 180,
                        },
                    },
                    timeout=120,
                    stream=True,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    status_code = exc.response.status_code
                    try:
                        error_data = exc.response.json()
                        error_message = (
                            error_data.get("error", {}).get("message")
                            or "Unknown Gemini API error."
                        )
                    except ValueError:
                        error_message = "Unknown Gemini API error."

                    raise LLMGenerationError(
                        f"Gemini API error ({status_code}): "
                        f"{error_message}"
                    ) from exc

                raise LLMGenerationError(
                    "The cloud language model could not "
                    "generate a response."
                ) from exc

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue

                payload = line[5:].strip()
                if payload == "[DONE]":
                    continue

                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                candidates = data.get("candidates")
                if not isinstance(candidates, list) or not candidates:
                    continue

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])

                if not isinstance(parts, list):
                    continue

                for part in parts:
                    text = part.get("text")
                    if isinstance(text, str) and text:
                        yield text

        except LLMGenerationError:
            raise
        except requests.RequestException as exc:
            raise LLMGenerationError(
                "The cloud language model could not "
                "complete the streamed response."
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