-- EVEZ VCL Sensory Accumulation — Supabase migration
-- Run in Supabase SQL editor

-- Brain state: evolving physics params per VCL (persists across restarts)
CREATE TABLE IF NOT EXISTS vcl_brain_state (
  vcl_id TEXT PRIMARY KEY,
  params JSONB NOT NULL DEFAULT '{}',
  total_messages BIGINT DEFAULT 0,
  peak_viewers INTEGER DEFAULT 0,
  last_active TIMESTAMPTZ DEFAULT NOW(),
  session_start TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sensory event log: every chat mutation event
CREATE TABLE IF NOT EXISTS vcl_sensory_log (
  id BIGSERIAL PRIMARY KEY,
  vcl_id TEXT NOT NULL REFERENCES vcl_brain_state(vcl_id),
  event_type TEXT NOT NULL DEFAULT 'chat_mutation',
  author TEXT,
  message TEXT,
  params_snapshot JSONB,
  sentiment_score FLOAT,
  viewer_count INTEGER DEFAULT 0,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS vcl_sensory_vcl_ts_idx ON vcl_sensory_log (vcl_id, timestamp DESC);

-- Viewer registry: who has interacted, how much
CREATE TABLE IF NOT EXISTS vcl_viewer_sessions (
  id BIGSERIAL PRIMARY KEY,
  vcl_id TEXT NOT NULL,
  channel_id TEXT,
  display_name TEXT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  message_count INTEGER DEFAULT 0,
  total_mutations INTEGER DEFAULT 0,
  UNIQUE(vcl_id, channel_id)
);

-- RLS
ALTER TABLE vcl_brain_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE vcl_sensory_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE vcl_viewer_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_brain" ON vcl_brain_state FOR SELECT USING (true);
CREATE POLICY "service_all_brain" ON vcl_brain_state FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "public_read_log" ON vcl_sensory_log FOR SELECT USING (true);
CREATE POLICY "service_all_log" ON vcl_sensory_log FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "public_read_viewers" ON vcl_viewer_sessions FOR SELECT USING (true);
CREATE POLICY "service_all_viewers" ON vcl_viewer_sessions FOR ALL USING (auth.role() = 'service_role');

-- Seed initial brain states
INSERT INTO vcl_brain_state (vcl_id) VALUES ('fire'),('ocean'),('neural'),('void'),('prime')
ON CONFLICT (vcl_id) DO NOTHING;
