#!/usr/bin/env bash
# deploy-all.sh — EVEZ Meme Bus v2 full stack
set -euo pipefail

echo "▶ [DEPLOY] EVEZ Meme Bus v2 + OpenClaw EventSpine"

# ── 1. Directory scaffold ──────────────────────────────────────────────
mkdir -p src/memory \
         assets/input_images \
         assets/corpus_templates \
         assets/output_memes \
         assets/audio \
         assets/drafts \
         data logs bus agents service loops scripts

# ── 2. Python deps ─────────────────────────────────────────────────────
pip install --quiet \
  fastapi "uvicorn[standard]" \
  pillow apscheduler openai tweepy \
  python-multipart python-dotenv requests

# ── 3. Launch agents as background processes ────────────────────────────
echo "▶ Starting agents..."
python3 -m agents.image_ingestor    >> logs/image_ingestor.log   2>&1 &
echo $! > logs/image_ingestor.pid

python3 -m agents.vision_agent      >> logs/vision_agent.log     2>&1 &
echo $! > logs/vision_agent.pid

python3 -m agents.twitter_context   >> logs/twitter_context.log  2>&1 &
echo $! > logs/twitter_context.pid

python3 -m agents.corpus_agent      >> logs/corpus_agent.log     2>&1 &
echo $! > logs/corpus_agent.pid

python3 -m agents.caption_agent     >> logs/caption_agent.log    2>&1 &
echo $! > logs/caption_agent.pid

python3 -m agents.guard_agent       >> logs/guard_agent.log      2>&1 &
echo $! > logs/guard_agent.pid

python3 -m agents.layout_agent      >> logs/layout_agent.log     2>&1 &
echo $! > logs/layout_agent.pid

python3 -m agents.publisher         >> logs/publisher.log        2>&1 &
echo $! > logs/publisher.pid

python3 -m agents.audio_narrator    >> logs/audio_narrator.log   2>&1 &
echo $! > logs/audio_narrator.pid

python3 -m agents.twitter_poster    >> logs/twitter_poster.log   2>&1 &
echo $! > logs/twitter_poster.pid

python3 -m agents.spine_bridge      >> logs/spine_bridge.log     2>&1 &
echo $! > logs/spine_bridge.pid

python3 -m loops.fire_sync          >> logs/fire_sync.log        2>&1 &
echo $! > logs/fire_sync.pid

# ── 4. FastAPI control plane ────────────────────────────────────────────
echo "▶ Starting FastAPI on :8000..."
uvicorn service.api:app --host 0.0.0.0 --port 8000 \
  --reload >> logs/api.log 2>&1 &
echo $! > logs/api.pid

echo ""
echo "✅ EVEZ Meme Bus v2 running. Logs → logs/"
echo "   API          → http://localhost:8000/healthz"
echo "   Queue status → http://localhost:8000/queue-status"
echo "   Drafts       → http://localhost:8000/drafts"
echo "   Published    → http://localhost:8000/published"
echo "   FIRE feed    → http://localhost:8000/fire-feed"
echo "   Spine tail   → http://localhost:8000/spine"
echo "   Audio list   → http://localhost:8000/audio"
echo ""
echo "   Set AUTO_POST_MEMES=true to enable X auto-posting"
echo "   Set SPINE_LOG_PATH to point at your fire_log.jsonl"
