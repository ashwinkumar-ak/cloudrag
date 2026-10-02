ALTER TABLE chat_messages
ADD COLUMN IF NOT EXISTS citations JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_chat_messages_citations
    ON chat_messages USING GIN (citations);
