CREATE TABLE IF NOT EXISTS spreadsheet_rows (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sheet_name TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    data JSONB NOT NULL,
    display_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, sheet_name, row_number)
);

CREATE INDEX IF NOT EXISTS idx_spreadsheet_rows_document
    ON spreadsheet_rows(document_id);

CREATE INDEX IF NOT EXISTS idx_spreadsheet_rows_sheet
    ON spreadsheet_rows(document_id, sheet_name);
