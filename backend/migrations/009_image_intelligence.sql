CREATE TABLE IF NOT EXISTS document_images (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id)
);

CREATE INDEX IF NOT EXISTS idx_document_images_document_id
    ON document_images(document_id);
