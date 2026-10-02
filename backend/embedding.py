import time

from sentence_transformers import SentenceTransformer

from backend.metrics import EMBEDDING_LATENCY


class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text must not be empty")

        start = time.perf_counter()

        try:
            embedding = self.model.encode(text)

            if len(embedding) != 384:
                raise ValueError(
                    f"Expected 384 dimensions, got {len(embedding)}"
                )

            return embedding.tolist()
        finally:
            duration = time.perf_counter() - start
            EMBEDDING_LATENCY.observe(duration)
