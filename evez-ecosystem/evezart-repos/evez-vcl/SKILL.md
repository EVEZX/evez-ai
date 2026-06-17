# SKILL.md — EVEZ Plugin Manifest v2
id: evez-vcl
name: Visual Cognition Layer
version: 0.3.0
schema: 2

runtime:
  port: 8002
  base_url: https://evez-vcl.onrender.com
  health_endpoint: /health
  skills_endpoint: /skills

capabilities:
  - render_artifact
  - manifest_load
  - visual_emit
  - consciousness_frame

fire_events:
  - FIRE_PLUGIN_ACTIVATED
  - FIRE_PLUGIN_DEACTIVATED
  - FIRE_PLUGIN_ERROR
  - FIRE_VCL_RENDER
  - FIRE_VCL_MANIFEST_LOADED

dependencies:
  - evez-os

auth:
  type: api_key
  header: X-EVEZ-API-KEY

termux:
  start_cmd: "python3 vcl_server.py --serve --port 8002"
  pm2_name: evez-vcl
