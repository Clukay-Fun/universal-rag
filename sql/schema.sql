-- ============================================
-- Universal RAG 通用内核 - 数据库 Schema
-- 执行: psql -U postgres -d universal-rag -f sql/schema.sql
-- ============================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- region 助手配置表
-- ============================================

CREATE TABLE IF NOT EXISTS assistants (
    assistant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    system_prompt TEXT,           -- 助手专属 system prompt
    config JSONB DEFAULT '{}',    -- 额外配置
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS assistants_name_idx ON assistants(name);
CREATE INDEX IF NOT EXISTS assistants_is_active_idx ON assistants(is_active);

-- endregion
-- ============================================

-- ============================================
-- region 助手数据源配置表
-- ============================================

CREATE TABLE IF NOT EXISTS assistant_datasources (
    datasource_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assistant_id UUID NOT NULL REFERENCES assistants(assistant_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    ds_type VARCHAR(50) NOT NULL, -- 'postgresql', 'mysql', 'api', etc.
    connection_config JSONB NOT NULL, -- 加密存储连接信息
    table_schema JSONB,           -- 表结构描述 (供 LLM 理解)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS assistant_datasources_assistant_id_idx 
    ON assistant_datasources(assistant_id);

-- endregion
-- ============================================

-- ============================================
-- region 文档表 (RAG 知识库)
-- ============================================

CREATE TABLE IF NOT EXISTS documents (
    doc_id BIGSERIAL PRIMARY KEY,
    assistant_id UUID REFERENCES assistants(assistant_id) ON DELETE SET NULL,
    title TEXT,
    file_name TEXT,
    source_type TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_assistant_id_idx ON documents(assistant_id);

CREATE TABLE IF NOT EXISTS document_nodes (
    node_id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES document_nodes(node_id) ON DELETE SET NULL,
    level INT NOT NULL,
    title TEXT,
    content TEXT,
    path TEXT[],
    embedding VECTOR(1024),
    order_index INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS document_nodes_doc_id_idx ON document_nodes(doc_id);
CREATE INDEX IF NOT EXISTS document_nodes_parent_id_idx ON document_nodes(parent_id);
CREATE INDEX IF NOT EXISTS document_nodes_embedding_idx ON document_nodes
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- endregion
-- ============================================

-- ============================================
-- region 对话会话表
-- ============================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NULL,
    assistant_id UUID REFERENCES assistants(assistant_id) ON DELETE SET NULL,
    title TEXT,
    message_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations JSONB NULL,
    token_count INT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chat_messages_session_idx ON chat_messages(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS chat_sessions_created_idx ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS chat_sessions_assistant_id_idx ON chat_sessions(assistant_id);

-- endregion
-- ============================================

-- ============================================
-- region 默认助手初始化
-- ============================================

INSERT INTO assistants (assistant_id, name, description, system_prompt, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '默认助手',
    '通用知识问答助手',
    '你是一个专业的知识库问答助手。请根据用户问题，结合检索到的知识库内容，给出准确、有帮助的回答。如果无法从知识库找到答案，请诚实告知用户。',
    TRUE
) ON CONFLICT (assistant_id) DO NOTHING;

-- endregion
-- ============================================
