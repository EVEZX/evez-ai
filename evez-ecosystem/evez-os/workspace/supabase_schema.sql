-- EVEZ-OS Gen 3 Supabase Schema
-- Phase 0: per-user fork instances + skin registry

CREATE TABLE IF NOT EXISTS player_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  fork_round INTEGER NOT NULL,
  fork_V NUMERIC(10, 6) NOT NULL,
  current_round INTEGER NOT NULL,
  V_global NUMERIC(10, 6) NOT NULL,
  fire_count INTEGER DEFAULT 0,
  ceiling_tick INTEGER DEFAULT 0,
  truth_plane TEXT DEFAULT 'CANONICAL',
  reality_module TEXT DEFAULT 'number_theory_v1',
  skin_id TEXT DEFAULT 'terminal-canonical',
  epoch INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS spine_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id UUID REFERENCES player_instances(id),
  user_id TEXT NOT NULL,
  round_k INTEGER NOT NULL,
  N INTEGER NOT NULL,
  N_factored TEXT,
  tau INTEGER,
  omega_k INTEGER,
  poly_c NUMERIC(10, 6),
  fire BOOLEAN DEFAULT FALSE,
  fire_number INTEGER,
  delta_V NUMERIC(10, 6),
  V_new NUMERIC(10, 6),
  truth_plane TEXT DEFAULT 'CANONICAL',
  branch TEXT,
  tokens JSONB,
  committed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skins (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  description TEXT,
  author TEXT,
  price_usd NUMERIC(8, 2) DEFAULT 0,
  license TEXT DEFAULT 'MIT',
  skin_json JSONB NOT NULL,
  downloads INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skin_ownership (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  skin_id TEXT REFERENCES skins(id),
  acquired_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS console_war_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id UUID REFERENCES player_instances(id),
  user_id TEXT NOT NULL,
  epoch INTEGER DEFAULT 0,
  epoch_name TEXT,
  failure_mode TEXT,
  evez_counter TEXT,
  falsifier_passed BOOLEAN DEFAULT FALSE,
  unlocked_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_player_instances_user ON player_instances(user_id);
CREATE INDEX idx_spine_events_user ON spine_events(user_id);
CREATE INDEX idx_spine_events_round ON spine_events(round_k);
CREATE INDEX idx_skin_ownership_user ON skin_ownership(user_id);

INSERT INTO skins (id, name, version, description, author, price_usd, license, skin_json)
VALUES ('terminal-canonical', 'Terminal Canonical', '0.1.0',
  'Default EVEZ-OS terminal skin. Canonical math visible at all times.',
  'EVEZ', 0.00, 'MIT', '{}'::jsonb)
ON CONFLICT (id) DO NOTHING;
