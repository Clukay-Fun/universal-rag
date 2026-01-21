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

CREATE INDEX IF NOT EXISTS document_nodes_path_gin_idx ON document_nodes USING gin (path);
CREATE INDEX IF NOT EXISTS document_nodes_title_idx ON document_nodes(title);
CREATE INDEX IF NOT EXISTS document_nodes_content_idx ON document_nodes USING gin (to_tsvector('simple', content));
