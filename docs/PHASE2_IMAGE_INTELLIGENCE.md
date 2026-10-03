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

## Migrations

Phase 2 standalone images uses migration 009. This embedded-image increment adds migration 010.

Apply, in order if not already applied:

```text
backend/migrations/009_image_intelligence.sql
backend/migrations/010_embedded_document_images.sql
```

Do not rerun migrations 001–008. If 009 is already applied, apply only 010.

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

## Embedded document images increment

PDF, DOCX, and PPTX uploads now extract embedded raster images (up to 8 images per document), store the originals in protected storage, analyze each image with Gemini, and append the visual descriptions to the searchable document text. Retrieved documents can send up to 3 relevant stored images to Gemini during answer generation.

Migration 010 removes the one-image-per-document constraint from migration 009 and records source labels and image ordering. Standalone image documents continue to work unchanged.

## Current Phase 2 boundary

This increment does not add OCR-only indexing, image thumbnails in the Sources panel, or Gemini Files API lifecycle management. Those remain separate future enhancements.

## Visual evidence in Sources

Phase 2 now exposes protected previews for images that are directly associated with a retrieved citation. When a source chunk is backed by a standalone image or an embedded image, the citation panel can show the actual visual evidence before the text evidence.

The preview endpoint is authenticated and enforces document ownership. No public storage URL is exposed to the browser.
