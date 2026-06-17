# SKILL.md — EVEZ Plugin Manifest v2
id: surething-offline
name: SureThing Offline
version: 0.1.0
schema: 2

runtime:
  port: 8420
  base_url: http://localhost:8420
  health_endpoint: /health
  skills_endpoint: /skills

capabilities:
  - chat_query
  - task_queue
  - draft_store
  - event_spine_read
  - memory_search

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_TASK_ENQUEUED
  - FIRE_MEMORY_WRITTEN

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "bash bootstrap.sh"
  pm2_name: surething-offline
