from prometheus_client import Counter, Histogram, generate_latest


REQUEST_COUNT = Counter(
    "cloudrag_requests_total",
    "Total number of HTTP requests",
)

REQUEST_LATENCY = Histogram(
    "cloudrag_request_latency_seconds",
    "HTTP request latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 75, 100),
)

RAG_REQUEST_COUNT = Counter(
    "cloudrag_rag_requests_total",
    "Total number of RAG question requests",
)

RAG_REQUEST_LATENCY = Histogram(
    "cloudrag_rag_request_latency_seconds",
    "RAG question request latency in seconds",
    buckets=(1, 2.5, 5, 10, 25, 50, 75, 100, 180),
)

EMBEDDING_LATENCY = Histogram(
    "cloudrag_embedding_latency_seconds",
    "Embedding generation latency in seconds",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

LLM_LATENCY = Histogram(
    "cloudrag_llm_latency_seconds",
    "LLM generation latency in seconds",
    buckets=(1, 2.5, 5, 10, 25, 50, 75, 100, 180),
)

DOCUMENT_INGESTION_COUNT = Counter(
    "cloudrag_documents_ingested_total",
    "Total number of successfully ingested documents",
)

DOCUMENT_INGESTION_LATENCY = Histogram(
    "cloudrag_document_ingestion_latency_seconds",
    "Document ingestion latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50),
)


def get_metrics():
    return generate_latest()