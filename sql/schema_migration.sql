ALTER TABLE enterprises
    DROP COLUMN IF EXISTS is_state_owned,
    DROP COLUMN IF EXISTS auto_filled,
    DROP COLUMN IF EXISTS data_source;

ALTER TABLE performances
    DROP COLUMN IF EXISTS is_individual,
    DROP COLUMN IF EXISTS party_a_credit_code;

ALTER TABLE performances
    RENAME COLUMN sign_date TO sign_date_norm;

ALTER TABLE performances
    ADD COLUMN IF NOT EXISTS sign_date_raw TEXT;

ALTER TABLE performances
    RENAME COLUMN contract_type TO project_type;

ALTER TABLE performances
    ALTER COLUMN amount TYPE DECIMAL(12, 2) USING amount::DECIMAL(12, 2),
    ALTER COLUMN amount SET NOT NULL,
    ALTER COLUMN subject_amount TYPE DECIMAL(12, 2) USING subject_amount::DECIMAL(12, 2),
    ALTER COLUMN fee_method TYPE TEXT,
    ALTER COLUMN team_member TYPE TEXT;
