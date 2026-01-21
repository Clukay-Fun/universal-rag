ALTER TABLE document_nodes ADD COLUMN IF NOT EXISTS structure_model TEXT;
ALTER TABLE document_nodes ADD COLUMN IF NOT EXISTS structure_payload JSONB;
ALTER TABLE document_nodes ADD COLUMN IF NOT EXISTS structure_raw TEXT;
ALTER TABLE document_nodes ADD COLUMN IF NOT EXISTS structure_error TEXT;
ALTER TABLE document_nodes ADD COLUMN IF NOT EXISTS structure_created_at TIMESTAMP WITHOUT TIME ZONE;

DO $merge$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'document_structures'
    ) THEN
        WITH roots AS (
            SELECT node_id,
                   doc_id,
                   ROW_NUMBER() OVER (
                       PARTITION BY doc_id
                       ORDER BY COALESCE(order_index, 0), node_id
                   ) AS rn
            FROM document_nodes
            WHERE parent_id IS NULL
        )
        UPDATE document_nodes AS dn
        SET structure_model = ds.model_name,
            structure_payload = ds.payload,
            structure_raw = ds.raw_text,
            structure_error = ds.error,
            structure_created_at = ds.created_at
        FROM document_structures AS ds
        JOIN roots AS r
          ON r.doc_id = ds.doc_id
         AND r.rn = 1
        WHERE dn.node_id = r.node_id;

        DROP TABLE document_structures;
    END IF;
END $merge$;
