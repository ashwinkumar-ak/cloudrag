CREATE TABLE chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE,
    role TEXT NOT NULL
        CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id
    ON chat_messages(session_id);

CREATE INDEX idx_chat_messages_created_at
    ON chat_messages(created_at);

CREATE INDEX idx_chat_sessions_updated_at
    ON chat_sessions(updated_at DESC);