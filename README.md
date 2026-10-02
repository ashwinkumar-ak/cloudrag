# CloudRAG — Production-style Document Intelligence Platform

CloudRAG is a full-stack Retrieval-Augmented Generation (RAG) platform for uploading documents, asking grounded questions, analyzing spreadsheets, comparing documents, and evaluating retrieval quality.

It is designed as a production-style application rather than a model demo, with authentication, user-level data ownership, persistent document storage, ingestion tracking, interactive citations, streaming answers, rate limiting, security headers, evaluation tooling, and separate local/cloud execution paths.

## Live Demo

**Frontend:** https://cloudrag-cyan.vercel.app/

The public deployment runs independently of the local development machine.

## Architecture

![CloudRAG Architecture](docs/cloudrag-architecture.png)

### Local development

```text
Browser
  ↓
React + Vite + Nginx
  ↓
FastAPI
  ├── PostgreSQL + pgvector
  ├── Local file storage
  └── Ollama → Qwen3:4b
```

### Cloud deployment

```text
Internet
  ↓
Vercel
  ↓
Render → FastAPI
          ├── Supabase PostgreSQL + pgvector
          ├── Supabase Storage
          └── Gemini API
```

The local and cloud environments intentionally use different infrastructure. The local environment is optimized for development and offline-capable experimentation, while the cloud environment uses managed services and Gemini.

## Key Features

| # | Feature | What it provides |
|---|---|---|
| 1 | Original file storage | Keeps uploaded source files available for download |
| 2 | Production ingestion | Background processing with persistent stages, progress and failures |
| 3 | Interactive citations | Answers link back to source documents and retrieved evidence |
| 4 | Spreadsheet intelligence | Structured Excel/CSV storage, filtering and deterministic calculations |
| 5 | RAG evaluation | Retrieval hit rate, reference coverage, exact match and latency metrics |
| 6 | Security hardening | Authentication, ownership checks, rate limiting, upload limits and security headers |
| 7 | Streaming responses | Progressive AI answer generation using SSE |
| 8 | Document comparison | Side-by-side evidence-based comparison of two documents |

## Technology Stack

### Frontend
- React
- Vite
- Nginx
- Responsive desktop/mobile UI

### Backend
- Python
- FastAPI
- Uvicorn
- JWT authentication
- PostgreSQL access
- SSE streaming

### Data and retrieval
- PostgreSQL
- pgvector
- Vector embeddings
- User-scoped document/chunk retrieval
- Structured spreadsheet rows

### Local AI
- Ollama
- Qwen3:4b

### Cloud AI
- Google Gemini
- Gemini embeddings
- Gemini Flash-Lite generation

### Cloud infrastructure
- Vercel — frontend hosting
- Render — backend hosting
- Supabase — PostgreSQL/pgvector and object storage
- Google Gemini API — cloud inference

### Development
- Docker
- Docker Compose
- Pytest
- GitHub Actions

## Document Pipeline

```text
Upload
  ↓
Persistent document record
  ↓
Original file storage
  ↓
Parsing
  ↓
Text extraction
  ↓
Chunking
  ↓
Embedding generation
  ↓
pgvector storage
  ↓
Semantic retrieval
  ↓
LLM answer generation
  ↓
Citations + persisted chat history
```

Spreadsheet files additionally follow a structured path:

```text
Excel / CSV
  ↓
Typed row extraction
  ↓
Structured JSONB rows
  ↓
Deterministic filtering/calculation
  ↓
Result rows used as evidence
```

## Security

CloudRAG includes:

- JWT authentication
- Per-user document ownership
- Per-user chat/session ownership
- Protected document download
- Protected search and answer endpoints
- Upload size limits
- Sliding-window rate limiting
- Separate limits for authentication, search, chat and uploads
- `429 Too Many Requests` responses with `Retry-After`
- `413 Payload Too Large` for oversized uploads
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Permissions-Policy`
- HSTS in production

The production configuration keeps secrets outside the repository.

## API Surface

Representative endpoint groups include:

```text
/auth/register
/auth/login
/auth/me

/documents
/documents/{id}
/documents/{id}/download
/documents/{id}/retry
/documents/compare

/search
/ask
/ask/stream

/evaluation/*
/health
/live
/ready
/metrics
```

Swagger/OpenAPI is available from the FastAPI deployment at:

```text
/docs
```

## RAG Evaluation

The evaluation panel supports small, repeatable test sets and reports:

- Retrieval hit rate
- Reference-answer coverage
- Exact-match rate
- Average latency
- p95 latency
- Individual test-case results
- Generated answers

Evaluation is intentionally lightweight and does not require a separate LLM judge.

## Local Development

### Requirements

- Docker Desktop
- Python 3.14+
- Ollama
- Qwen3:4b

### Start Ollama

```powershell
ollama pull qwen3:4b
ollama serve
```

### Start CloudRAG

```powershell
docker compose up --build
```

Local services:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Swagger:  http://localhost:8000/docs
Ollama:   http://localhost:11434
```

### Stop

```powershell
docker compose down
```

PostgreSQL data is persisted in the Docker volume.

## Cloud Deployment

The production architecture uses:

```text
Vercel
  └── React/Vite frontend

Render
  └── FastAPI backend

Supabase
  ├── PostgreSQL + pgvector
  └── Private document storage

Google Gemini
  ├── Embeddings
  └── LLM generation
```

Required production configuration includes:

```text
DATABASE_URL
JWT_SECRET_KEY
FRONTEND_URL
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
GEMINI_MODEL
GEMINI_EMBEDDING_MODEL
GEMINI_API_BASE_URL
```

Secrets must be configured in the hosting provider rather than committed to Git.

## Project Structure

```text
cloudrag/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── security.py
│   ├── database.py
│   ├── ingestion.py
│   ├── chunking.py
│   ├── document_parser.py
│   ├── embedding.py
│   ├── llm.py
│   ├── rag.py
│   ├── metrics.py
│   ├── models.py
│   ├── repositories/
│   └── migrations/
├── frontend/
├── tests/
├── docs/
├── .github/workflows/
├── compose.yaml
├── pyproject.toml
└── README.md
```

## Verification

The project was verified progressively during implementation with:

- Python compilation checks
- Focused unit tests
- Authentication testing
- Upload and download testing
- Ingestion failure/retry testing
- Citation persistence testing
- Spreadsheet calculation testing
- RAG evaluation testing
- Rate-limit testing
- Upload-size testing
- Security-header testing
- Streaming response testing
- Document comparison testing
- Cloud deployment verification
- Mobile UI verification

## Engineering Notes

A major design goal was to keep deterministic application logic separate from generative AI behavior.

For example:

- File ownership is enforced by the application and database queries.
- Spreadsheet filtering and arithmetic are deterministic.
- Retrieval produces explicit evidence.
- The LLM is responsible for natural-language synthesis rather than silently inventing application state.
- Citations are persisted with assistant messages.
- Local and cloud inference are separated behind the application layer.

This makes the system easier to test, debug and deploy.

## Current Scope

CloudRAG currently focuses on:

- Document-grounded question answering
- Source citations
- Spreadsheet analysis
- Document comparison
- Retrieval evaluation
- Production-style authentication and security
- Local and cloud deployment

Potential future work could include OCR for scanned documents, richer evaluation datasets, background job queues, advanced observability, and more document formats.

## License

CloudRAG is licensed under the MIT License
