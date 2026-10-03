# Phase 2 — Multi-Image Visual Reasoning

This increment extends CloudRAG's working image intelligence pipeline so Gemini can reason across multiple relevant figures/images retrieved from the same document or from multiple selected documents.

## What changed

- Retrieved image-aware chunks can contribute distinct images to one multimodal request.
- Up to 4 relevant images are supplied to Gemini per question.
- Different figures from the same document are kept distinct instead of collapsing to the first image.
- Each image is labeled with its visual-evidence number, source label, and document filename before the image payload.
- Prompts explicitly allow comparison, sequence, relationships, trends, and synthesis across supplied images.
- Existing standalone-image and embedded-image behavior remains unchanged when only one image is relevant.
- No database migration is required; this uses the existing `document_images` schema from migrations 009–010.

## Example questions

For a document containing several charts/figures:

- "Compare the two charts and explain the main trend."
- "What changed between Figure 1 and Figure 2?"
- "Using the figures and surrounding text, summarize the progression shown."
- "Which figure provides evidence for the conclusion in the document?"

## Deployment

1. Extract this ZIP over the current `cloudrag-v2` working tree.
2. Do **not** run another Supabase migration.
3. Commit and push to `cloudrag-v2`.
4. Let Render redeploy the backend.
5. Redeploy Vercel if the deployment system detects the frontend/docs changes; no frontend code change is required for this increment.

## Validation

The package includes focused tests for multi-image selection and visual-input labeling, plus the existing image/model/evaluation test suites.
