ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT 'gemini-3.5-flash-lite';

CREATE INDEX IF NOT EXISTS idx_chat_sessions_model
ON chat_sessions(model);
