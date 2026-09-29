from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "cloudrag_requests_total",
    "Total number of HTTP requests",
)

REQUEST_LATENCY = Histogram(
    "cloudrag_request_latency_seconds",
    "HTTP request latency in seconds",
)


def get_metrics():
    return generate_latest()