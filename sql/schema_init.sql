CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE enterprises (
    credit_code VARCHAR(18) NOT NULL,
    company_name VARCHAR(255),
    business_scope TEXT,
    industry VARCHAR(100),
    enterprise_type VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT enterprises_pkey PRIMARY KEY (credit_code)
);

CREATE TABLE lawyers (
    id INTEGER,
    name VARCHAR(50),
    id_card VARCHAR(18),
    license_no VARCHAR(50),
    resume TEXT,
    resume_embedding VECTOR(1024),
    id_card_image VARCHAR(255),
    degree_image VARCHAR(255),
    diploma_image VARCHAR(255),
    license_image VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE performances (
    id INTEGER NOT NULL,
    file_name VARCHAR(255),
    party_a VARCHAR(255),
    party_a_id VARCHAR(50),
    contract_number INTEGER,
    amount DECIMAL(12, 2) NOT NULL,
    fee_method TEXT,
    sign_date_norm DATE,
    sign_date_raw TEXT,
    project_type VARCHAR(50),
    project_detail TEXT,
    subject_amount DECIMAL(12, 2),
    opponent VARCHAR(255),
    team_member TEXT,
    summary TEXT,
    image_data BYTEA,
    image_count INTEGER,
    raw_text TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    embedding VECTOR(1024),
    CONSTRAINT performances_pkey PRIMARY KEY (id),
    CONSTRAINT performances_amount_nonnegative CHECK (amount >= 0),
    CONSTRAINT performances_subject_amount_nonnegative CHECK (
        subject_amount IS NULL OR subject_amount >= 0
    )
);

CREATE INDEX IF NOT EXISTS enterprises_company_name_idx ON enterprises(company_name);
CREATE INDEX IF NOT EXISTS enterprises_industry_idx ON enterprises(industry);
CREATE INDEX IF NOT EXISTS enterprises_enterprise_type_idx ON enterprises(enterprise_type);

CREATE INDEX IF NOT EXISTS lawyers_name_idx ON lawyers(name);
CREATE INDEX IF NOT EXISTS lawyers_license_no_idx ON lawyers(license_no);
CREATE INDEX IF NOT EXISTS lawyers_id_card_idx ON lawyers(id_card);
CREATE INDEX IF NOT EXISTS lawyers_resume_embedding_idx ON lawyers
    USING ivfflat (resume_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS performances_party_a_idx ON performances(party_a);
CREATE INDEX IF NOT EXISTS performances_party_a_id_idx ON performances(party_a_id);
CREATE INDEX IF NOT EXISTS performances_project_type_idx ON performances(project_type);
CREATE INDEX IF NOT EXISTS performances_sign_date_norm_idx ON performances(sign_date_norm);
CREATE INDEX IF NOT EXISTS performances_amount_idx ON performances(amount);
CREATE INDEX IF NOT EXISTS performances_embedding_idx ON performances
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
