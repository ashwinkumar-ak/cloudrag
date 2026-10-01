# CloudRAG

**Production-style Document Intelligence and Retrieval-Augmented Generation (RAG) platform built with FastAPI, React, PostgreSQL/pgvector, local AI models, and a cloud deployment path.**

CloudRAG is a RAG platform designed around production-oriented concerns such as authentication, multi-user data isolation, vector retrieval, hybrid search, observability, health checks, automated testing, and containerized deployment. It has two deployment modes: a fully local development stack and a public cloud deployment.

## Public Application

The current cloud deployment is publicly accessible at:

**https://cloudrag-cyan.vercel.app/**

The public application uses the cloud architecture described below and does not depend on the developer's local Windows PC.

## Features

### Document Intelligence
- Document upload and ingestion
- Text extraction
- Sentence-aware chunking
- Local embedding generation in the local deployment
- Gemini Embedding 2 in the cloud deployment
- PostgreSQL + pgvector storage
- Semantic vector retrieval
- Keyword retrieval
- Hybrid retrieval
- Document-level filtering
- Source citations in RAG responses

### RAG and Chat
- Local LLM-powered question answering in the local deployment
- Ollama integration for local development
- `qwen3:4b` local model
- Gemini 3.5 Flash-Lite in the cloud deployment
- Retrieval-grounded answers
- Conversation history
- Persistent chat sessions
- Multiple chat sessions
- Session deletion
- Context-aware follow-up questions

### Authentication and Security
- User registration and login
- JWT access tokens
- Password hashing with `scrypt`
- Protected API endpoints
- User-owned documents and chat sessions
- User-scoped vector retrieval
- Database-level ownership enforcement

### Observability
- Liveness, readiness, and health endpoints
- PostgreSQL and AI service health monitoring
- Prometheus-compatible metrics
- HTTP request and latency metrics
- Document ingestion metrics
- LLM latency metrics
- Docker healthchecks

### Engineering
- FastAPI REST API
- React + Vite frontend
- Docker Compose
- PostgreSQL + pgvector
- Automated pytest test suite
- GitHub Actions CI
- Persistent PostgreSQL storage
- Containerized backend deployment

## Architecture

CloudRAG has a local architecture for development and a separate cloud architecture for public access.

### Local Architecture

```text
                         Browser
                            |
                            v
                 +---------------------+
                 | React + Vite        |
                 | Nginx               |
                 | Docker :5173        |
                 +----------+----------+
                            |
                            v
                 +---------------------+
                 | FastAPI Backend     |
                 | Docker :8000        |
                 +-----+----------+-----+
                       |          |
                       v          v
              +-------------+  +----------------+
              | PostgreSQL  |  | Ollama         |
              | + pgvector  |  | Windows Host   |
              | Docker      |  | :11434         |
              | :5432       |  | qwen3:4b       |
              +-------------+  +----------------+
```

### Cloud Architecture

```text
                         Internet
                            |
                  +---------+---------+
                  |                   |
                  v                   v
          +---------------+   +---------------+
          | Vercel        |   | Render        |
          | React/Vite    |-->| FastAPI       |
          | Frontend      |   | Backend       |
          +---------------+   +-------+-------+
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                +----------------+        +----------------+
                | Supabase       |        | Gemini APIs    |
                | PostgreSQL     |        | Embedding 2    |
                | + pgvector     |        | 3.5 Flash-Lite |
                +----------------+        +----------------+
```

The cloud deployment is independent of the local Windows machine. Local Ollama and Docker resources are used only for local development and testing.

### RAG Pipeline

```text
Document
   |
   v
Text Extraction
   |
   v
Text Chunking
   |
   v
Embeddings
   |
   +---- Local: Sentence Transformers
   |
   +---- Cloud: Gemini Embedding 2
   |
   v
PostgreSQL + pgvector
   |
   v
Hybrid Retrieval
   |
   +---- Semantic Search
   |
   +---- Keyword Search
   |
   v
Ranked Context
   |
   v
LLM Generation
   |
   +---- Local: Ollama / qwen3:4b
   |
   +---- Cloud: Gemini 3.5 Flash-Lite
   |
   v
Grounded Answer + Citations
```

## Technology Stack

### Backend
- Python 3.14
- FastAPI
- Pydantic Settings
- psycopg
- PostgreSQL
- pgvector
- Sentence Transformers (local deployment)
- PyMuPDF
- python-docx
- python-pptx
- openpyxl
- PyJWT
- Prometheus Client
- Requests

### Frontend
- React
- Vite
- Nginx

### AI
- Local: Ollama + Qwen3 4B
- Local: Sentence Transformers embeddings
- Cloud: Gemini Embedding 2
- Cloud: Gemini 3.5 Flash-Lite

### Infrastructure
- Docker
- Docker Compose
- PostgreSQL + pgvector
- GitHub Actions

### Testing
- pytest
- FastAPI/Starlette test client

## Project Structure

```text
cloudrag/
├── backend/
│   ├── auth.py
│   ├── chunking.py
│   ├── config.py
│   ├── database.py
│   ├── document_parser.py
│   ├── embedding.py
│   ├── health.py
│   ├── ingestion.py
│   ├── llm.py
│   ├── main.py
│   ├── metrics.py
│   ├── models.py
│   ├── rag.py
│   ├── text_processing.py
│   ├── Dockerfile
│   ├── migrations/
│   └── repositories/
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── tests/
├── docs/
├── .github/
│   └── workflows/
│       └── ci.yml
├── compose.yaml
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

# Getting Started

CloudRAG can be run locally with Ollama or accessed through the public cloud deployment above. The local setup is useful for development, testing, and running the full stack on a Windows machine.

## Prerequisites

Install:
- Docker Desktop
- Python 3.14+
- Git
- Ollama

Pull the local LLM:

```powershell
ollama pull qwen3:4b
```

Verify Ollama:

```powershell
ollama list
```

## Environment Configuration

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Generate a JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value into:

```env
JWT_SECRET_KEY=your-generated-secret
```

Never commit `.env`.

# Run with Docker Compose

Start the complete application:

```powershell
docker compose up -d --build
```

Check the containers:

```powershell
docker compose ps
```

Expected services:

```text
cloudrag-postgres
cloudrag-backend
cloudrag-frontend
```

Frontend:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

# Public Cloud Deployment

CloudRAG has a separate public cloud deployment designed so that the application can be accessed over the internet without using the developer's local Windows machine.

## Public Application

**Live application:**

```text
https://cloudrag-cyan.vercel.app/
```

## Cloud Architecture

```text
                         Internet
                            |
                  +---------+---------+
                  |                   |
                  v                   v
          +---------------+   +---------------+
          | Vercel        |   | Render        |
          | React + Vite  |-->| FastAPI       |
          | Frontend      |   | Backend       |
          +---------------+   +-------+-------+
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                +----------------+        +----------------+
                | Supabase       |        | Gemini APIs    |
                | PostgreSQL     |        | Embedding 2    |
                | + pgvector     |        | 3.5 Flash-Lite |
                +----------------+        +----------------+
```

### Cloud services

| Service | Role | Cloud responsibility |
|---|---|---|
| Vercel | Frontend hosting | React + Vite production application |
| Render | Backend hosting | FastAPI API, authentication, ingestion and RAG orchestration |
| Supabase | Database | PostgreSQL + pgvector for users, documents, chunks, embeddings and chat data |
| Gemini | AI services | Gemini Embedding 2 for embeddings and Gemini 3.5 Flash-Lite for answer generation |

## Cloud AI Configuration

The cloud deployment does not use Ollama. The cloud backend uses Gemini through environment variables such as:

```text
GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

The database connection is configured through `DATABASE_URL` and points to the Supabase Session Pooler, allowing the Render backend to reach the cloud PostgreSQL instance.

The frontend is configured with the deployed backend API URL through `VITE_API_URL`, while the backend uses `FRONTEND_URL` for CORS configuration.

## Deployment Isolation

The public deployment is completely independent of the local development environment:

```text
Local PC                         Public Cloud
--------                         ------------
Ollama + Qwen3 4B               Gemini APIs
Sentence Transformers            Gemini Embedding 2
Local PostgreSQL                 Supabase PostgreSQL
Docker Desktop                   Render
Local React                      Vercel
```

The public application therefore does **not** consume the local PC's CPU, GPU, RAM, Ollama instance, Docker containers, or local database. The Windows machine can be offline while the public application remains available, subject to the cloud providers' service availability and quotas.

## Cloud Branch

Cloud-specific changes are maintained separately from the stable local setup in:

```text
deployment/cloud-hosted
```

This keeps the local Ollama-based architecture intact while allowing the cloud deployment to use managed infrastructure and Gemini APIs.

## Cloud Database

The public application uses a separate Supabase PostgreSQL database with the `pgvector` extension. It is independent of the local Docker PostgreSQL database.

The cloud database contains the same application schema and migrations but is not populated by copying the local development data. User accounts, documents, chunks, embeddings, and chat sessions created through the public application are stored in the cloud database.

## Public Deployment Flow

```text
User opens https://cloudrag-cyan.vercel.app/
                |
                v
        Vercel React frontend
                |
                v
        Render FastAPI backend
          /       |        \
         /        |         \
        v         v          v
   Supabase    Gemini     JWT/Auth
   pgvector     APIs       + RAG
```

The public deployment is intended for small-scale usage and portfolio/demo access. Service quotas, resource limits, cold starts, database capacity, and API rate limits depend on the respective cloud providers.

# Local Development

Start PostgreSQL and the frontend:

```powershell
docker compose up -d postgres frontend
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
uvicorn backend.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Frontend:

```text
http://localhost:5173
```

# API

## Public endpoints

```text
GET /health
GET /live
GET /ready
GET /metrics

POST /auth/register
POST /auth/login
GET  /auth/me
```

## Protected document endpoints

```text
GET    /documents
POST   /documents
DELETE /documents/{document_id}
```

## Protected retrieval endpoints

```text
POST /search
POST /ask
```

## Protected chat endpoints

```text
GET    /sessions
POST   /sessions
GET    /sessions/{session_id}/messages
DELETE /sessions/{session_id}
```

Interactive local API documentation:

```text
http://localhost:8000/docs
```

The public frontend is available at:

```text
https://cloudrag-cyan.vercel.app/
```

# Authentication

CloudRAG uses JWT-based authentication.

```text
Register/Login
     |
     v
Password verification
     |
     v
JWT access token
     |
     v
Authorization: Bearer <token>
     |
     v
Authenticated API request
```

Passwords are stored using salted `scrypt` password hashes.

The backend derives the authenticated `user_id` from the JWT rather than accepting a client-supplied user identifier.

Documents, chat sessions, messages, and retrieval results are scoped to the authenticated user.

# Retrieval

CloudRAG uses a hybrid retrieval strategy combining:

1. Semantic vector similarity
2. Keyword matching

The resulting candidates are combined into a hybrid ranking before being supplied to the RAG layer.

# RAG

```text
Question
   |
   v
Query embedding
   |
   v
Hybrid retrieval
   |
   v
Relevant document chunks
   |
   v
Conversation context
   |
   v
Ollama
   |
   v
Structured answer
   |
   v
Answer + source citations
```

The RAG prompt instructs the configured model to answer using the supplied document excerpts rather than relying on outside knowledge. In local mode this is Qwen3 4B through Ollama; in cloud mode this is Gemini 3.5 Flash-Lite.

# Monitoring

### Liveness

```text
GET /live
```

Indicates whether the application process is alive.

### Readiness

```text
GET /ready
```

Checks whether required dependencies are ready.

### Health

```text
GET /health
```

Reports application and dependency health.

### Metrics

```text
GET /metrics
```

Exposes Prometheus-compatible metrics.

Tracked metrics include HTTP request activity, HTTP latency, document ingestion, and LLM generation latency.

# Testing

Run the complete test suite:

```powershell
pytest -q
```

Current test suite:

```text
11 passed
```

GitHub Actions also runs the Python test suite automatically for pushes and pull requests targeting `main`.

# Docker Services

| Service | Purpose | Port |
|---|---|---:|
| frontend | React application served by Nginx | 5173 |
| backend | FastAPI API and RAG orchestration | 8000 |
| postgres | PostgreSQL + pgvector | 5432 |
| Ollama | Local LLM inference | 11434 |

Ollama intentionally remains on the Windows host while the application services run in Docker.

The backend reaches the host Ollama instance through:

```text
http://host.docker.internal:11434
```

# Data Persistence

PostgreSQL uses a Docker named volume:

```text
postgres_data
```

This preserves application data across normal container recreation.

Do not use:

```powershell
docker compose down -v
```

unless you intentionally want to delete the database volume and all stored data.

# Deployment Model

CloudRAG supports both a local development stack and a public cloud deployment.

### Local

The local stack uses:

- PostgreSQL + pgvector
- Sentence Transformer embeddings
- Ollama
- Qwen3 4B
- Docker + Docker Compose
- React + Vite + Nginx

### Public Cloud

The public stack uses:

- Vercel
- Render
- Supabase PostgreSQL + pgvector
- Gemini Embedding 2
- Gemini 3.5 Flash-Lite

The two environments are intentionally separated. The public deployment does not consume the local PC's CPU, GPU, Ollama instance, Docker containers, or local database.

# Current Deployment Model

### Local

```text
Windows Host
│
├── Ollama
│   └── qwen3:4b
│
└── Docker Desktop
    │
    ├── PostgreSQL + pgvector
    ├── FastAPI backend
    └── React + Nginx
```

### Public Cloud

```text
Internet
│
├── Vercel
│   └── React + Vite frontend
│
└── Render
    └── FastAPI backend
        ├── Supabase PostgreSQL + pgvector
        └── Gemini APIs
```

Public application:

**https://cloudrag-cyan.vercel.app/**

The public deployment is independent of the local Windows machine.

# Engineering Goals

CloudRAG was built to demonstrate practical experience across:

- Backend API development
- REST API design
- Authentication
- Database design
- PostgreSQL
- Vector databases
- Retrieval-Augmented Generation
- Embeddings
- Local and cloud LLM inference
- Hybrid search
- Frontend development
- Docker
- Container orchestration
- Health monitoring
- Metrics
- Automated testing
- CI/CD
- Application architecture
- Data isolation and ownership

# Future Improvements

Potential next-stage improvements include:

- Background ingestion workers
- Async document processing
- Reranking models
- Redis-backed job queues
- Distributed tracing
- Advanced document metadata
- More sophisticated access-control policies
- Horizontal scaling
- Streaming LLM responses
- Evaluation datasets and RAG quality benchmarks

These are intentionally outside the current core implementation.

# License

This project is currently intended as a personal learning and portfolio project.
