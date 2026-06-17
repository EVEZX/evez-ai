# SKILL.md — EVEZ Plugin Manifest v2
id: lord-evez
name: LORD EVEZ Dashboard
version: 1.0.0
schema: 2

runtime:
  port: 3000
  base_url: http://localhost:3000
  health_endpoint: /api/live
  skills_endpoint: /api/live

capabilities:
  - metrics_live_bridge
  - webhook_ingest
  - dashboard_render
  - control_policy_issue

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_DASHBOARD_SYNC
  - FIRE_POLICY_ISSUE_CREATED

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "npx vercel dev"
  pm2_name: lord-evez
