CREATE TABLE IF NOT EXISTS purchase_guide_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    summary TEXT,
    pros TEXT,  -- JSON array
    cons TEXT,  -- JSON array
    score INTEGER
);