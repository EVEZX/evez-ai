# SKILL.md — EVEZ Plugin Manifest v2
id: polymarket-speedrun
name: Polymarket Speedrun
version: 0.1.0
schema: 2

runtime:
  port: 8005
  base_url: http://localhost:8005
  health_endpoint: /health
  skills_endpoint: /skills

capabilities:
  - scan_markets
  - evaluate_edge
  - place_position
  - get_pnl

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_TRADE_PLACED
  - FIRE_TRADE_SETTLED
  - FIRE_TRADE_REVENUE
  - FIRE_RISK_LIMIT_HIT

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "python main.py --dry-run"
  pm2_name: polymarket-speedrun
