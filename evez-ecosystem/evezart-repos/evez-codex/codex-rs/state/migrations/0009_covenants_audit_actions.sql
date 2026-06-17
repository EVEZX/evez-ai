CREATE TABLE IF NOT EXISTS covenants (
    version TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    actor TEXT NOT NULL,
    action_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    covenant_version TEXT NOT NULL,
    event_id TEXT,
    intent_id TEXT,
    FOREIGN KEY(covenant_version) REFERENCES covenants(version)
);

CREATE INDEX IF NOT EXISTS audit_actions_timestamp_idx
    ON audit_actions (timestamp);

CREATE INDEX IF NOT EXISTS audit_actions_scope_idx
    ON audit_actions (scope);
