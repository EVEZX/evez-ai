# SKILL.md — EVEZ Plugin Manifest v2
id: evez-meme-bus
name: EVEZ Meme Bus
version: 0.1.0
schema: 2

runtime:
  port: 8004
  base_url: http://localhost:8004
  health_endpoint: /healthz
  skills_endpoint: /queue-status

capabilities:
  - publish_meme
  - queue_status
  - event_tail
  - draft_feed

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_MEME_PUBLISHED
  - FIRE_MEME_VIRAL
  - FIRE_MEME_REVENUE

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "./deploy-all.sh"
  pm2_name: evez-meme-bus
