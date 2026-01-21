CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NULL,
    title TEXT,
    message_count INT DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations JSONB NULL,
    token_count INT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS chat_messages_session_idx
ON chat_messages(session_id, created_at DESC)
INCLUDE (role, content);

CREATE INDEX IF NOT EXISTS chat_sessions_created_idx ON chat_sessions(created_at);
