ALTER TABLE document_images
    DROP CONSTRAINT IF EXISTS document_images_document_id_key;

ALTER TABLE document_images
    ADD COLUMN IF NOT EXISTS source_label TEXT,
    ADD COLUMN IF NOT EXISTS image_index INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_document_images_document_index
    ON document_images(document_id, image_index);
