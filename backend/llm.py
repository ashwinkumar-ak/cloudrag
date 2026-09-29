import requests

from backend.metrics import LLM_LATENCY
import time


class LLMService:
    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        start = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                },
                timeout=120,
            )

            response.raise_for_status()

            answer = response.json()["response"]

            return self._clean_answer(answer)
        finally:
            duration = time.perf_counter() - start
            LLM_LATENCY.observe(duration)

    def _clean_answer(self, answer: str) -> str:
        if "</think>" in answer:
            answer = answer.split("</think>", 1)[1]

        return answer.strip()