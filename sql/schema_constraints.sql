ALTER TABLE enterprises
    ALTER COLUMN credit_code SET NOT NULL,
    ADD CONSTRAINT enterprises_pkey PRIMARY KEY (credit_code);

ALTER TABLE performances
    ALTER COLUMN id SET NOT NULL,
    ADD CONSTRAINT performances_pkey PRIMARY KEY (id),
    ADD CONSTRAINT performances_amount_nonnegative CHECK (amount >= 0),
    ADD CONSTRAINT performances_subject_amount_nonnegative CHECK (
        subject_amount IS NULL OR subject_amount >= 0
    );
