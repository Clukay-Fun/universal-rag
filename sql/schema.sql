-- ============================================
-- Universal RAG 数据库完整 Schema
-- 执行: psql "${DATABASE_URL}" -f sql/schema.sql
-- ============================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 企业信息表
-- ============================================
CREATE TABLE IF NOT EXISTS enterprises (
    credit_code VARCHAR(18) NOT NULL PRIMARY KEY,
    company_name VARCHAR(255),
    business_scope TEXT,
    industry VARCHAR(100),
    enterprise_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS enterprises_company_name_idx ON enterprises(company_name);
CREATE INDEX IF NOT EXISTS enterprises_industry_idx ON enterprises(industry);

-- ============================================
-- 律师信息表
-- ============================================
CREATE TABLE IF NOT EXISTS lawyers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    id_card VARCHAR(18),
    license_no VARCHAR(50),
    resume TEXT,
    resume_embedding VECTOR(1024),
    id_card_image VARCHAR(255),
    degree_image VARCHAR(255),
    diploma_image VARCHAR(255),
    license_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS lawyers_name_idx ON lawyers(name);
CREATE INDEX IF NOT EXISTS lawyers_license_no_idx ON lawyers(license_no);
CREATE INDEX IF NOT EXISTS lawyers_resume_embedding_idx ON lawyers
    USING ivfflat (resume_embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 业绩合同表 (智能匹配数据源)
-- ============================================
CREATE TABLE IF NOT EXISTS performances (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255),
    party_a VARCHAR(255),
    party_a_id VARCHAR(50),
    contract_number INTEGER,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
    fee_method TEXT,
    sign_date_norm DATE,
    sign_date_raw TEXT,
    project_type VARCHAR(50),
    project_detail TEXT,
    subject_amount DECIMAL(12, 2) CHECK (subject_amount >= 0),
    opponent VARCHAR(255),
    team_member TEXT,
    summary TEXT,
    image_data BYTEA,
    image_count INTEGER,
    raw_text TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS performances_party_a_idx ON performances(party_a);
CREATE INDEX IF NOT EXISTS performances_project_type_idx ON performances(project_type);
CREATE INDEX IF NOT EXISTS performances_sign_date_norm_idx ON performances(sign_date_norm);
CREATE INDEX IF NOT EXISTS performances_amount_idx ON performances(amount);
CREATE INDEX IF NOT EXISTS performances_embedding_idx ON performances
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 文档表 (RAG 知识库)
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    doc_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    party_a_name TEXT,
    party_a_credit_code TEXT,
    party_a_source TEXT,
    source_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

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

-- ============================================
-- 对话会话表
-- ============================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NULL,
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

-- ============================================
-- 智能匹配表
-- ============================================
CREATE TABLE IF NOT EXISTS tender_requirements (
    tender_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    raw_text TEXT NOT NULL,
    constraints JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contract_matches (
    match_id BIGSERIAL PRIMARY KEY,
    tender_id BIGINT NOT NULL REFERENCES tender_requirements(tender_id) ON DELETE CASCADE,
    contract_id BIGINT NOT NULL REFERENCES performances(id) ON DELETE CASCADE,
    score DECIMAL(6, 4) NOT NULL CHECK (score >= 0),
    reasons JSONB DEFAULT '[]'::JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contract_matches_tender_id_idx ON contract_matches(tender_id);
CREATE INDEX IF NOT EXISTS contract_matches_contract_id_idx ON contract_matches(contract_id);
