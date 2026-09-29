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