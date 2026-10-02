# CloudRAG 2.0 — Phase 1: Multi-Model Support

This phase adds model selection to the existing CloudRAG V2 RAG experience without changing the embedding pipeline.

## Supported generation models

- `gemini-3.5-flash-lite` — default, fast/cost-efficient RAG chat
- `gemini-3.5-flash` — higher-capability generation for more complex questions

Model availability, quotas, and pricing are controlled by the Google AI project behind `GEMINI_API_KEY`.

## What changed

- Central model registry and validation
- Authenticated `GET /models` endpoint
- Model selection per chat session
- Persistent selected model on `chat_sessions`
- Model selector in the CloudRAG chat header
- Streaming and non-streaming `/ask` requests honor the selected model
- Document comparison honors the selected model
- Existing Gemini Embedding 2 / 768-dimensional retrieval remains unchanged

## Database migration

Run `backend/migrations/008_multi_model_support.sql` in the CloudRAG V2 Supabase SQL Editor before deploying the updated backend.

The migration adds:

```sql
model TEXT NOT NULL DEFAULT 'gemini-3.5-flash-lite'
```

to `chat_sessions`.

Existing conversations automatically use Gemini 3.5 Flash-Lite.

## Deployment order

1. Apply migration 008 to the V2 Supabase project.
2. Replace the V2 source with this package.
3. Commit and push the `cloudrag-v2` branch.
4. Let Render and Vercel redeploy.
5. Sign in and confirm the model selector appears in the chat header.
6. Test a question with each model.
7. Start a new chat and verify the selected model persists after reload.

No changes are required to the Gemini embedding configuration or the `vector(768)` database column.

## Included Feature 5 completion

This Phase 1 package also includes the verified Evaluation UI completion:
- Evaluation navigation/tab
- RAG evaluation runner and result display
- Knowledge Base document IDs for evaluation-case references

The Evaluation UI is frontend-only and does not alter the V2 Gemini Embedding 2 configuration.


## Frontend model selector

The Chat header includes a model selector backed by `GET /models` and `PUT /sessions/{session_id}/model`. The selected model is persisted per chat session and is restored when the conversation is reopened.
