from fastapi import FastAPI, HTTPException

from backend.config import settings
from backend.health import get_health_status, is_ready

from backend.embedding import EmbeddingService
from backend.models import AskRequest, AskResponse, SearchRequest, SearchResult
from backend.repositories.chunks import ChunkRepository

from fastapi import FastAPI, File, HTTPException, UploadFile
from backend.ingestion import IngestionService

from fastapi.middleware.cors import CORSMiddleware

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST

from backend.metrics import get_metrics

import time

from backend.metrics import REQUEST_COUNT, REQUEST_LATENCY

from backend.rag import RAGService

embedding_service = EmbeddingService()
chunk_repository = ChunkRepository()
ingestion_service = IngestionService()
rag_service = RAGService()

app = FastAPI(
    title="CloudRAG API",
    description="Production-style document intelligence and RAG API",
    version="0.1.0",
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(duration)

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "service": settings.app_name,
        "environment": settings.environment,
        **get_health_status(),
    }

@app.get("/live")
def liveness_check():
    return {
        "status": "alive"
        }

@app.get("/ready")
def readiness_check():
    if not is_ready():
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        )
    return {
        "status": "ready"
        }

@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest):
    query_embedding = embedding_service.embed(request.query)

    rows = chunk_repository.search_chunks(
        embedding=query_embedding,
        limit=request.limit,
    )

    return [
        SearchResult(
            chunk_id=row[0],
            document_id=row[1],
            chunk_index=row[2],
            content=row[3],
            distance=float(row[4]),
        )
        for row in rows
    ]

@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    if file.content_type not in {
        "text/plain",
        "text/markdown",
    }:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are currently supported",
        )

    content = await file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded",
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document must not be empty",
        )

    try:
        document_id = ingestion_service.ingest_text(
            filename=file.filename,
            content_type=file.content_type,
            text=text,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {exc}",
        )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "completed",
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    answer, context = rag_service.answer(
        question=request.question,
        limit=request.limit,
    )

    return AskResponse(
        answer=answer,
        citations=context,
    )