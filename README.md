CloudRAG

Production-style Document Intelligence and Retrieval-Augmented Generation (RAG) platform built with FastAPI, React, PostgreSQL/pgvector, and local AI models.

CloudRAG is a zero-cost, locally deployable RAG platform designed around production-oriented concerns such as authentication, multi-user data isolation, vector retrieval, hybrid search, observability, health checks, automated testing, and containerized deployment.

Features

Document Intelligence

Document upload and ingestion

Text extraction

Sentence-aware chunking

Local embedding generation

PostgreSQL + pgvector storage

Semantic vector retrieval

Keyword retrieval

Hybrid retrieval

Document-level filtering

Source citations in RAG responses

RAG and Chat

Local LLM-powered question answering

Ollama integration

qwen3:4b local model

Retrieval-grounded answers

Conversation history

Persistent chat sessions

Multiple chat sessions

Session deletion

Context-aware follow-up questions

Authentication and Security

User registration and login

JWT access tokens

Password hashing with scrypt

Protected API endpoints

User-owned documents and chat sessions

User-scoped vector retrieval

Database-level ownership enforcement

Observability

Liveness, readiness, and health endpoints

PostgreSQL and Ollama health monitoring

Prometheus-compatible metrics

HTTP request and latency metrics

Document ingestion metrics

LLM latency metrics

Docker healthchecks

Engineering

FastAPI REST API

React + Vite frontend

Docker Compose

PostgreSQL + pgvector

Automated pytest test suite

GitHub Actions CI

Persistent PostgreSQL storage

Containerized backend deployment

Architecture

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

RAG Pipeline

Document
   |
   v
Text Extraction
   |
   v
Text Chunking
   |
   v
Local Embeddings
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
Ollama / qwen3:4b
   |
   v
Grounded Answer + Citations

Technology Stack

Backend

Python 3.14

FastAPI

Pydantic Settings

psycopg

PostgreSQL

pgvector

Sentence Transformers

PyMuPDF

python-docx

python-pptx

openpyxl

PyJWT

Prometheus Client

Requests

Frontend

React

Vite

Nginx

AI

Ollama

Qwen3 4B

Local sentence-transformer embeddings

Infrastructure

Docker

Docker Compose

PostgreSQL + pgvector

GitHub Actions

Testing

pytest

FastAPI/Starlette test client

Project Structure

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

Getting Started

Prerequisites

Install:

Docker Desktop

Python 3.14+

Git

Ollama

Pull the local LLM:

ollama pull qwen3:4b

Verify Ollama:

ollama list

Environment Configuration

Create .env from the example:

Copy-Item .env.example .env

Generate a JWT secret:

python -c "import secrets; print(secrets.token_urlsafe(48))"

Put the generated value into:

JWT_SECRET_KEY=your-generated-secret

Never commit .env.

Run with Docker Compose

Start the complete application:

docker compose up -d --build

Check the containers:

docker compose ps

Expected services:

cloudrag-postgres
cloudrag-backend
cloudrag-frontend

Frontend:

http://localhost:5173

Backend API:

http://localhost:8000

Swagger API documentation:

http://localhost:8000/docs

Local Development

Start PostgreSQL and the frontend:

docker compose up -d postgres frontend

Activate the virtual environment:

.\.venv\Scripts\Activate.ps1

Start FastAPI:

uvicorn backend.main:app --reload

Backend:

http://127.0.0.1:8000

Frontend:

http://localhost:5173

API

Public endpoints

GET /health
GET /live
GET /ready
GET /metrics

POST /auth/register
POST /auth/login
GET  /auth/me

Protected document endpoints

GET    /documents
POST   /documents
DELETE /documents/{document_id}

Protected retrieval endpoints

POST /search
POST /ask

Protected chat endpoints

GET    /sessions
POST   /sessions
GET    /sessions/{session_id}/messages
DELETE /sessions/{session_id}

Interactive API documentation:

http://localhost:8000/docs

Authentication

CloudRAG uses JWT-based authentication.

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

Passwords are stored using salted scrypt password hashes.

The backend derives the authenticated user_id from the JWT rather than accepting a client-supplied user identifier.

Documents, chat sessions, messages, and retrieval results are scoped to the authenticated user.

Retrieval

CloudRAG uses a hybrid retrieval strategy combining:

Semantic vector similarity

Keyword matching

The resulting candidates are combined into a hybrid ranking before being supplied to the RAG layer.

RAG

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

The RAG prompt instructs the local model to answer using the supplied document excerpts rather than relying on outside knowledge.

Monitoring

Liveness

GET /live

Indicates whether the application process is alive.

Readiness

GET /ready

Checks whether required dependencies are ready.

Health

GET /health

Reports application and dependency health.

Metrics

GET /metrics

Exposes Prometheus-compatible metrics.

Tracked metrics include HTTP request activity, HTTP latency, document ingestion, and LLM generation latency.

Testing

Run the complete test suite:

pytest -q

Current test suite:

11 passed

GitHub Actions also runs the Python test suite automatically for pushes and pull requests targeting main.

Docker Services

Service

Purpose

Port

frontend

React application served by Nginx

5173

backend

FastAPI API and RAG orchestration

8000

postgres

PostgreSQL + pgvector

5432

Ollama

Local LLM inference

11434

Ollama intentionally remains on the Windows host while the application services run in Docker.

The backend reaches the host Ollama instance through:

http://host.docker.internal:11434

Data Persistence

PostgreSQL uses a Docker named volume:

postgres_data

This preserves application data across normal container recreation.

Do not use:

docker compose down -v

unless you intentionally want to delete the database volume and all stored data.

Zero-Cost Design

CloudRAG is designed to run without paid cloud AI services.

The current architecture uses:

PostgreSQL locally

pgvector locally

Sentence Transformer embeddings locally

Ollama locally

Qwen3 4B locally

Docker locally

GitHub Actions for CI

No paid LLM API is required for the core application.

Current Deployment Model

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

This provides a production-style architecture while keeping the project at zero infrastructure cost.

Engineering Goals

CloudRAG was built to demonstrate practical experience across:

Backend API development

REST API design

Authentication

Database design

PostgreSQL

Vector databases

Retrieval-Augmented Generation

Embeddings

Local LLM inference

Hybrid search

Frontend development

Docker

Container orchestration

Health monitoring

Metrics

Automated testing

CI/CD

Application architecture

Data isolation and ownership

Future Improvements

Potential next-stage improvements include:

Background ingestion workers

Async document processing

Reranking models

Redis-backed job queues

Distributed tracing

Advanced document metadata

More sophisticated access-control policies

Cloud deployment

Horizontal scaling

Streaming LLM responses

Evaluation datasets and RAG quality benchmarks

These are intentionally outside the current core implementation.

License

This project is currently intended as a personal learning and portfolio project.