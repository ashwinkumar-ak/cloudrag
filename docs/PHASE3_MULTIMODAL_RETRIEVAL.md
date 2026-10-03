# CloudRAG V2 Phase 3 — Multimodal Retrieval

## Scope

Phase 3 adds Gemini Embedding 2 based multimodal retrieval to CloudRAG V2. Text queries and stored images share the same 768-dimensional embedding space, allowing a text question to retrieve both document chunks and visually relevant images.

## Included

- Gemini Embedding 2 image embeddings for standalone images.
- Gemini Embedding 2 image embeddings for embedded PDF/DOCX/PPTX images.
- `document_images.embedding vector(768)` storage.
- HNSW cosine index for image vectors.
- Cross-modal RAG retrieval: text chunks + image evidence are merged into one ranked context.
- Search endpoint returns document and visual matches together.
- Existing image-aware answering continues to send retrieved visual evidence to Gemini.
- Existing citations and protected image previews remain intact.
- Knowledge Base action to build/rebuild the visual search index for images uploaded before Phase 3.

## Migration

Apply only:

```sql
-- backend/migrations/011_multimodal_embeddings.sql
```

No existing chunk embedding migration is required. Existing 768-dimensional Gemini Embedding 2 text vectors remain unchanged.

## Existing documents

Images that already existed before Phase 3 have a NULL image embedding until **Build visual search index** is run from the Knowledge Base panel. New image uploads are embedded automatically during ingestion.

## Retrieval behavior

- Text query → text embedding.
- The same query embedding is compared against document chunk vectors and image vectors.
- The strongest document and visual candidates are merged and ranked by cosine similarity.
- When a visual result is used for RAG, its visual description is supplied as context and the original protected image is supplied to Gemini for multimodal reasoning.

## Validation

Backend compilation and the existing multimodal/model tests pass. Frontend dependency installation/build should be run in the normal Vercel/CI environment after extraction.

## Phase 3 reliability fixes in this build

This build includes two retrieval hardening changes before implementation:

1. **Exact visual evidence association** — a normal text chunk no longer inherits an arbitrary image merely because its document contains images. Embedded-image chunks attach only to the matching `image_index`; standalone-image chunks attach only to their standalone image.
2. **Larger candidate pool before final selection** — text and image retrieval each collect up to `max(limit * 3, 12)` candidates before the unified ranking/selection step. This reduces the chance that one modality is discarded too early.

These changes do not alter the Phase 1/Phase 2 user-facing architecture or the Phase 3 database schema.

## Implementation order

1. Apply migrations through `011_multimodal_embeddings.sql` in order if this is a fresh V2 database.
2. Deploy the updated backend to Render.
3. Deploy the frontend to Vercel.
4. For images that existed before Phase 3, run **Build visual search index** once from Knowledge Base.
5. Verify a standalone image, an embedded PDF/DOCX/PPTX image, and a normal text-only chunk from the same document all retrieve the correct evidence.
