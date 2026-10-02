from backend.evaluation import RAGEvaluationService


def test_answer_coverage_ignores_common_stop_words():
    score = RAGEvaluationService._answer_coverage(
        "Prometheus stores numeric time series metrics",
        "Prometheus stores metrics and exposes numeric time series data",
    )
    assert score == 1.0


def test_answer_coverage_is_partial_when_reference_terms_are_missing():
    score = RAGEvaluationService._answer_coverage(
        "Prometheus integrates with Alertmanager for alerting",
        "Prometheus stores time series metrics",
    )
    assert 0 < score < 1


def test_exact_match_normalizes_whitespace_and_case():
    assert RAGEvaluationService._exact_match(
        "Prometheus stores metrics", "  prometheus   stores metrics  "
    )
