-- 描述: 创建智能匹配相关表
-- 文件: sql/migrations/002_tender_matching.sql

-- 招标需求表
CREATE TABLE IF NOT EXISTS tender_requirements (
    tender_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    raw_text TEXT NOT NULL,
    constraints JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 匹配结果表
CREATE TABLE IF NOT EXISTS contract_matches (
    match_id BIGSERIAL PRIMARY KEY,
    tender_id BIGINT NOT NULL REFERENCES tender_requirements(tender_id) ON DELETE CASCADE,
    contract_id BIGINT NOT NULL REFERENCES contract_data(contract_id) ON DELETE CASCADE,
    score DECIMAL(6, 4) NOT NULL CHECK (score >= 0),
    reasons JSONB DEFAULT '[]'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS contract_matches_tender_id_idx ON contract_matches(tender_id);
CREATE INDEX IF NOT EXISTS contract_matches_contract_id_idx ON contract_matches(contract_id);
