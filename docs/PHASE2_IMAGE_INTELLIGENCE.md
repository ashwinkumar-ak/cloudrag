# CloudRAG V2 Phase 2 — Image Intelligence

Phase 2 adds image-aware document intelligence without changing the existing Phase 1 RAG, evaluation, comparison, authentication, spreadsheet, citation, or multi-model flows.

## What it adds

- Upload JPEG, PNG, and WebP images into the existing Knowledge Base.
- Store the original image in the existing protected document storage.
- Analyze the image with Gemini multimodal input during ingestion.
- Persist a searchable visual description and image metadata.
- Embed the visual description into the existing pgvector pipeline.
- When an image is retrieved for a question, send the original image to Gemini together with the text RAG context.
- Support image-aware answers through both normal `/ask` and `/ask/stream`.
- Keep image ownership protected through the existing document/user ownership model.

Google documents that Gemini supports image understanding through inline image data and the Files API; inline data is appropriate for smaller requests, while the Files API is recommended for larger or repeatedly reused media. CloudRAG Phase 2 keeps the original image in Supabase Storage and sends retrieved images as inline data to the selected Gemini model for the current request. This keeps the architecture simple and avoids adding Gemini Files API lifecycle management in this phase.

## Migration

Apply only:

```text
backend/migrations/009_image_intelligence.sql
```

Do not rerun migrations 001–008.

## Supported image types

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

The existing 20 MB document limit applies; image uploads have an additional 8 MB limit so multimodal requests remain within practical inline-image request limits.

## Processing flow

```text
Image upload
   ↓
Supabase Storage
   ↓
Gemini multimodal analysis
   ↓
Visual description
   ↓
pgvector embedding
   ↓
Normal CloudRAG retrieval
   ↓
Relevant original image + text context
   ↓
Gemini Flash / Flash-Lite
   ↓
Answer + Sources
```

## Verification

1. Apply migration 009 in the V2 Supabase project.
2. Deploy backend to Render.
3. Deploy frontend to Vercel.
4. Upload a PNG/JPEG/WebP image to Knowledge Base.
5. Wait for `completed` ingestion.
6. Confirm the image has a document ID.
7. Ask a question whose answer depends on visible image content.
8. Test with both Gemini 3.5 Flash-Lite and Gemini 3.5 Flash.
9. Confirm the answer and Sources appear.
10. Delete the image and confirm it disappears from the Knowledge Base.

## Phase 2 scope boundary

This phase intentionally starts with standalone image documents. Embedded images inside PDFs, DOCX, and PPTX are not automatically extracted yet; that can be added as a later Phase 2 increment without changing the 009 schema.
