# CloudRAG

Production-style Document Intelligence and Retrieval-Augmented Generation (RAG) platform.

## Architecture

React Frontend
        |
        v
FastAPI Backend
        |
        v
PostgreSQL + pgvector

## RAG Pipeline

Document
→ Text extraction
→ Chunking
→ Embeddings
→ pgvector
→ Semantic search

## Technology Stack

- React + Vite
- FastAPI
- PostgreSQL
- pgvector
- sentence-transformers
- Docker
- GitHub Actions
- pytest
- Prometheus-compatible metrics

## Features

- Document upload
- Text chunking
- Local embeddings
- Vector search
- Health monitoring
- Prometheus metrics
- REST API
- React frontend
- Automated tests
- GitHub Actions CI

## API

- GET `/health`
- GET `/live`
- GET `/ready`
- GET `/metrics`
- POST `/documents`
- POST `/search`

## Local Development

Start infrastructure:

```powershell
docker compose up -d

Activate Python:

.\.venv\Scripts\Activate.ps1

Start backend:

uvicorn backend.main:app --reload

Frontend:

http://localhost:5173

API:

http://localhost:8000

Swagger:

http://localhost:8000/docs

Testing
python -m pytest
Monitoring

CloudRAG provides:

Liveness checks
Readiness checks
Database health checks
HTTP request metrics
HTTP latency metrics
Current Limitations
PDF ingestion is not implemented yet.
LLM answer generation is not connected yet.
Backend currently runs locally because the embedding dependency is large.
Authentication is not implemented.
Future Improvements
PDF/DOCX ingestion
RAG answer generation
Source citations
Reranking
Authentication
Background workers
Distributed tracing
Cloud deployment