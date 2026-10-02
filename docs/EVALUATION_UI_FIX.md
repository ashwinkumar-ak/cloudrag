# CloudRAG V1 Evaluation UI Fix

This update completes Feature 5 for the public cloud-hosted V1 application.

## Added
- Authenticated `POST /evaluation/run` API endpoint.
- User-scoped evaluation rate limit (10 runs/minute).
- Evaluation request validation for 1–10 cases.
- New **Evaluation** sidebar panel in the frontend.
- JSON case editor with example case.
- Retrieval hit rate, reference-answer coverage, exact-match rate, average latency, and p95 latency metrics.
- Per-case evaluation results and generated answers.

## Deployment

No database migration is required.

Deploy this package to the `deployment/cloud-hosted` branch / existing V1 Render service and Vercel deployment. Existing document, RAG, authentication, citation, spreadsheet, comparison, streaming, storage, and security functionality is unchanged.
