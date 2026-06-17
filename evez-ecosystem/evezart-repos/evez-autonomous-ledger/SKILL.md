# SKILL.md — EVEZ Plugin Manifest v2
id: evez-autonomous-ledger
name: EVEZ Autonomous Ledger
version: 0.1.0
schema: 2

runtime:
  port: 8006
  base_url: http://localhost:8006
  health_endpoint: /health
  skills_endpoint: /skills

capabilities:
  - ecosystem_state_read
  - decision_log_read
  - deployment_audit
  - agent_action_audit
  - synapse_report

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_LEDGER_UPDATED
  - FIRE_DEPLOYMENT_AUDIT
  - FIRE_AGENT_ACTION_LOGGED

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "python -m http.server 8006"
  pm2_name: evez-autonomous-ledger
