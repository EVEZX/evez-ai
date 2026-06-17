#!/usr/bin/env bash
# OS-EVEZ Demo Flow: upload fixtures → enable scheduler → assets discover → player sync
set -euo pipefail

BASE="http://127.0.0.1:8080"
DATA_DIR="${OG_DATA_DIR:-$HOME/og_data}"
DL_DIR="${HOME}/storage/downloads"

echo "[demo] Waiting for API to be ready..."
for i in $(seq 1 20); do
  curl -sf "$BASE/health" >/dev/null 2>&1 && break
  sleep 1
done

echo "[demo] Health check..."
curl -s "$BASE/health" | python -m json.tool

# Upload fixtures if present
for zip_name in evez_ops_console_bundle evez_pimped_duality_bundle evez_ultra_thought_viz fogglass_2min_plus_bundle; do
  zip_path="$DL_DIR/${zip_name}.zip"
  if [ -f "$zip_path" ]; then
    echo "[demo] Uploading fixture: $zip_name"
    curl -sf -F "file=@$zip_path" "$BASE/fixtures/upload?name=$zip_name" | python -m json.tool || echo "[warn] upload skipped"
  else
    echo "[demo] Fixture not found (skipping): $zip_path"
  fi
done

# Create first run
echo "[demo] Creating first run..."
curl -sf -X POST "$BASE/runs/create" -H "Content-Type: application/json"   -d "{"seed":888,"steps":35,"set_default":true}" | python -m json.tool || echo "[warn] run create skipped"

# Enable scheduler
echo "[demo] Enabling scheduler..."
curl -sf -X POST "$BASE/schedule" -H "Content-Type: application/json"   -d '"'"'{"enabled":true,"interval_seconds":600,"max_runs":1000000,"max_disk_mb":4096,"retention_runs":80}'"'" | python -m json.tool

# Assets discover
echo "[demo] Building assets map..."
curl -sf -X POST "$BASE/assets/discover" | python -m json.tool

# Register player
echo "[demo] Registering player..."
curl -sf -X POST "$BASE/players/register" -H "Content-Type: application/json"   -d '"'"'{"player_id":"steven"}'"'" | python -m json.tool

# Player sync
echo "[demo] Player sync..."
curl -sf "$BASE/players/sync/steven" | python -m json.tool

echo ""
echo "[demo] Done. Open in browser:"
echo "  http://127.0.0.1:8080/arcade"
echo "  http://127.0.0.1:8080/public-key.html"
echo "  http://127.0.0.1:8080/assets/map.html"
