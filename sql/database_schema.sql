CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    doc_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    source_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE document_nodes (
    node_id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES document_nodes(node_id) ON DELETE SET NULL,
    level INT NOT NULL,
    title TEXT,
    content TEXT,
    order_index INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE document_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    node_id BIGINT REFERENCES document_nodes(node_id) ON DELETE SET NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE chunk_embeddings (
    chunk_id BIGINT PRIMARY KEY REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX document_chunks_doc_id_idx ON document_chunks(doc_id);
CREATE INDEX document_nodes_doc_id_idx ON document_nodes(doc_id);
CREATE INDEX chunk_embeddings_embedding_idx ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE contract_data (
    contract_id BIGSERIAL PRIMARY KEY,
    contract_name TEXT,
    party_a TEXT NOT NULL,
    party_a_id TEXT,
    party_a_industry TEXT,
    is_state_owned BOOLEAN NOT NULL,
    is_individual BOOLEAN NOT NULL,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
    fee_method TEXT,
    sign_date_raw TEXT,
    sign_date_norm DATE,
    project_type TEXT,
    project_detail TEXT,
    subject_amount DECIMAL(12, 2) CHECK (subject_amount >= 0),
    opponent TEXT,
    team_member TEXT,
    summary TEXT,
    source_id TEXT,
    file_name TEXT,
    image_ref TEXT,
    prompt_id TEXT,
    prompt_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX contract_data_party_a_idx ON contract_data(party_a);
CREATE INDEX contract_data_project_type_idx ON contract_data(project_type);
CREATE INDEX contract_data_sign_date_norm_idx ON contract_data(sign_date_norm);

CREATE TABLE tender_requirements (
    tender_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    raw_text TEXT NOT NULL,
    constraints JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE contract_matches (
    match_id BIGSERIAL PRIMARY KEY,
    tender_id BIGINT NOT NULL REFERENCES tender_requirements(tender_id) ON DELETE CASCADE,
    contract_id BIGINT NOT NULL REFERENCES contract_data(contract_id) ON DELETE CASCADE,
    score DECIMAL(6, 4) NOT NULL CHECK (score >= 0),
    reasons JSONB DEFAULT '[]'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX contract_matches_tender_id_idx ON contract_matches(tender_id);
CREATE INDEX contract_matches_contract_id_idx ON contract_matches(contract_id);
