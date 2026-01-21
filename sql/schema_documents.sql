CREATE TABLE IF NOT EXISTS documents (
    doc_id BIGSERIAL PRIMARY KEY,
    title TEXT,
    file_name TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE IF NOT EXISTS document_nodes (
    node_id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES document_nodes(node_id) ON DELETE SET NULL,
    level INT NOT NULL,
    title TEXT,
    content TEXT,
    path TEXT[],
    structure_model TEXT,
    structure_payload JSONB,
    structure_raw TEXT,
    structure_error TEXT,
    structure_created_at TIMESTAMP WITHOUT TIME ZONE,
    order_index INT,
    created_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS document_nodes_doc_id_idx ON document_nodes(doc_id);
CREATE INDEX IF NOT EXISTS document_nodes_parent_id_idx ON document_nodes(parent_id);
