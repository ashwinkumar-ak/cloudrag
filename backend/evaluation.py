import re
import time
from statistics import mean

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "had", "in", "is", "it", "its", "of", "on", "or",
    "that", "the", "their", "this", "to", "was", "were", "what", "when",
    "where", "which", "who", "with", "how", "does", "do", "did", "than",
    "then", "into", "about", "can", "could", "should", "would", "will",
}


class RAGEvaluationService:
    def __init__(self):
        from backend.rag import RAGService
        self.rag_service = RAGService()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+", (text or "").lower())
        return {word for word in words if word not in STOP_WORDS and len(word) > 1}

    @classmethod
    def _answer_coverage(cls, expected: str, actual: str) -> float:
        expected_tokens = cls._tokens(expected)
        if not expected_tokens:
            return 1.0 if (actual or "").strip() else 0.0
        actual_tokens = cls._tokens(actual)
        return round(len(expected_tokens & actual_tokens) / len(expected_tokens), 4)

    @staticmethod
    def _exact_match(expected: str, actual: str) -> bool:
        normalize = lambda value: " ".join((value or "").lower().split())
        return normalize(expected) == normalize(actual)

    def run(self, cases: list[dict], user_id: int, default_limit: int = 5) -> dict:
        results = []
        latencies = []

        for index, case in enumerate(cases, start=1):
            started = time.perf_counter()
            try:
                answer, context = self.rag_service.answer(
                    question=case["question"],
                    user_id=user_id,
                    limit=case.get("limit", default_limit),
                    document_ids=case.get("document_ids") or None,
                    session_id=None,
                )

                latency_ms = round((time.perf_counter() - started) * 1000, 1)
                latencies.append(latency_ms)

                retrieved_document_ids = sorted({item["document_id"] for item in context})
                expected_document_ids = sorted(set(case.get("expected_document_ids") or []))
                retrieval_hit = (
                    True
                    if not expected_document_ids
                    else bool(set(retrieved_document_ids) & set(expected_document_ids))
                )

                results.append({
                    "case_number": index,
                    "question": case["question"],
                    "expected_answer": case["expected_answer"],
                    "generated_answer": answer,
                    "retrieved_document_ids": retrieved_document_ids,
                    "expected_document_ids": expected_document_ids,
                    "retrieval_hit": retrieval_hit,
                    "answer_coverage": self._answer_coverage(case["expected_answer"], answer),
                    "exact_match": self._exact_match(case["expected_answer"], answer),
                    "latency_ms": latency_ms,
                })
            except Exception as exc:
                latency_ms = round((time.perf_counter() - started) * 1000, 1)
                latencies.append(latency_ms)
                results.append({
                    "case_number": index,
                    "question": case["question"],
                    "expected_answer": case["expected_answer"],
                    "generated_answer": "",
                    "retrieved_document_ids": [],
                    "expected_document_ids": sorted(set(case.get("expected_document_ids") or [])),
                    "retrieval_hit": False,
                    "answer_coverage": 0.0,
                    "exact_match": False,
                    "latency_ms": latency_ms,
                    "error": str(exc),
                })

        successful = [item for item in results if "error" not in item]
        retrieval_cases = [item for item in successful if item["expected_document_ids"]]

        sorted_latencies = sorted(latencies)
        if sorted_latencies:
            p95_index = min(len(sorted_latencies) - 1, max(0, int(len(sorted_latencies) * 0.95) - 1))
            p95 = sorted_latencies[p95_index]
        else:
            p95 = 0.0

        return {
            "cases": len(results),
            "successful_cases": len(successful),
            "failed_cases": len(results) - len(successful),
            "retrieval_hit_rate": round(
                mean(item["retrieval_hit"] for item in retrieval_cases), 4
            ) if retrieval_cases else None,
            "reference_answer_coverage": round(
                mean(item["answer_coverage"] for item in successful), 4
            ) if successful else 0.0,
            "exact_match_rate": round(
                mean(item["exact_match"] for item in successful), 4
            ) if successful else 0.0,
            "average_latency_ms": round(mean(latencies), 1) if latencies else 0.0,
            "p95_latency_ms": p95,
            "results": results,
        }
