# CloudRAG Deployment Guide

## Production topology

```text
Vercel
  ↓ HTTPS
Render / FastAPI
  ├── Supabase PostgreSQL + pgvector
  ├── Supabase Storage
  └── Gemini API
```

## 1. Supabase

Create a project and enable the `vector` extension.

Create a private storage bucket named:

```text
documents
```

Run the project's SQL migrations in order.

The production `chunks.embedding` column uses:

```sql
vector(768)
```

Use the Supabase Session Pooler connection string when the hosting environment cannot reach the direct database endpoint.

## 2. Render

Deploy the backend from the repository.

Set production environment variables:

```text
DATABASE_URL=<Supabase Session Pooler URL>
JWT_SECRET_KEY=<long random secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

FRONTEND_URL=https://cloudrag-cyan.vercel.app

SUPABASE_SERVICE_ROLE_KEY=<Supabase service role key>

GEMINI_API_KEY=<Gemini API key>
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta

MAX_UPLOAD_SIZE_BYTES=20971520
SECURITY_HEADERS_ENABLED=true
```

Do not commit these values.

## 3. Vercel

Deploy the `frontend` application.

Configure the frontend's production API base URL to:

```text
https://cloudrag.onrender.com
```

The backend must allow the Vercel origin through `FRONTEND_URL`.

## 4. Post-deployment checks

Check:

```text
/live
/ready
/docs
```

Then verify:

1. Register a new account.
2. Log in.
3. Upload a small document.
4. Wait for ingestion to complete.
5. Ask a question.
6. Open a citation.
7. Download the original file.
8. Upload a spreadsheet.
9. Run a spreadsheet query.
10. Compare two completed documents.
11. Run an evaluation.
12. Verify streaming chat.
13. Verify mobile layout.
14. Confirm oversized uploads are rejected.
15. Confirm repeated requests eventually receive 429 responses.

## Production safety

Never publish:

- `.env`
- API keys
- JWT secrets
- Supabase service-role keys
- private uploaded documents
- local database volumes
- test documents containing sensitive information
