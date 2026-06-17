
-- EVEZ Emergent Spectral Mesh Intelligence schema
CREATE TABLE IF NOT EXISTS mesh_intelligence (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ DEFAULT NOW(),
    cycle_id    TEXT NOT NULL,
    phi         FLOAT8 NOT NULL,
    eta_star    FLOAT8 NOT NULL,
    omega       FLOAT8,
    n_repos     INTEGER,
    lambda_min  FLOAT8,
    gap_score   FLOAT8,
    regime      TEXT,
    ai_analysis JSONB,
    actions     JSONB,
    model_used  TEXT,
    platform_signals JSONB
);

CREATE TABLE IF NOT EXISTS mesh_actions (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ DEFAULT NOW(),
    cycle_id    TEXT NOT NULL,
    action_id   INTEGER,
    title       TEXT,
    target      TEXT,
    platform    TEXT,
    impact      TEXT,
    status      TEXT DEFAULT 'queued',
    result      JSONB
);

CREATE TABLE IF NOT EXISTS platform_health (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ DEFAULT NOW(),
    platform    TEXT NOT NULL,
    status      TEXT,
    details     JSONB
);

CREATE INDEX IF NOT EXISTS idx_mesh_ts ON mesh_intelligence (ts DESC);
CREATE INDEX IF NOT EXISTS idx_actions_status ON mesh_actions (status, ts DESC);

