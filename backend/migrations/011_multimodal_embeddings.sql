ALTER TABLE document_images
    ADD COLUMN IF NOT EXISTS embedding vector(768);

CREATE INDEX IF NOT EXISTS idx_document_images_embedding
    ON document_images USING hnsw (embedding vector_cosine_ops);
