CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_email_unique UNIQUE (email)
);


CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);


ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS user_id BIGINT;


ALTER TABLE documents
ADD COLUMN IF NOT EXISTS user_id BIGINT;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chat_sessions_user_id_fkey'
    ) THEN
        ALTER TABLE chat_sessions
        ADD CONSTRAINT chat_sessions_user_id_fkey
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE;
    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'documents_user_id_fkey'
    ) THEN
        ALTER TABLE documents
        ADD CONSTRAINT documents_user_id_fkey
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE;
    END IF;
END
$$;


CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id
    ON chat_sessions(user_id);


CREATE INDEX IF NOT EXISTS idx_documents_user_id
    ON documents(user_id);