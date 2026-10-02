ALTER TABLE documents
ADD COLUMN IF NOT EXISTS processing_stage TEXT NOT NULL DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS processing_progress INTEGER NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE documents
DROP CONSTRAINT IF EXISTS documents_processing_progress_check;

ALTER TABLE documents
ADD CONSTRAINT documents_processing_progress_check
CHECK (processing_progress BETWEEN 0 AND 100);

UPDATE documents
SET
    processing_stage = CASE
        WHEN status = 'completed' THEN 'completed'
        WHEN status = 'failed' THEN 'failed'
        WHEN status = 'processing' THEN 'processing'
        ELSE 'pending'
    END,
    processing_progress = CASE
        WHEN status = 'completed' THEN 100
        WHEN status = 'processing' THEN 10
        ELSE 0
    END
WHERE processing_stage = 'pending';
