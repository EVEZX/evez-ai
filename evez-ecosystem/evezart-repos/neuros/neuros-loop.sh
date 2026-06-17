#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# NEUROS AUTONOMOUS LOOP — The full self-sustaining cycle
# Runs every 30 min. No human needed. $0/month.
#
# Cycle: COLLECT → TRAIN → BUILD → DEPLOY → HEAL → SYNC → REPEAT
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

NEUROS_HOME="/home/openclaw/evez-ecosystem/neuros"
TRAINING_DIR="$NEUROS_HOME/training"
LOG="/tmp/neuros-loop.log"
TS=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "[$TS] 🧠 NEUROS autonomous cycle start" >> "$LOG"

# ─── 1. COLLECT — Gather new data from repos, conversations, skills ───
echo "[$TS] 📥 Collecting training data..." >> "$LOG"
python3 "$TRAINING_DIR/self-train.py" >> "$LOG" 2>&1

# ─── 2. HEAL — Restart any down services ───
echo "[$TS] 🩺 Health check..." >> "$LOG"
for svc in openclaw-gateway evez-provider evez-omega evez-filter evez-services-hub neuros; do
  if ! systemctl --user is-active --quiet "$svc" 2>/dev/null; then
    systemctl --user restart "$svc" 2>/dev/null
    echo "[$TS] 🔧 Restarted $svc" >> "$LOG"
  fi
done

# ─── 3. DISCOVER — Auto-discover new repos ───
if command -v gh &>/dev/null; then
  for org in EvezArt EVEZX; do
    gh api "/users/$org/repos?per_page=100" --jq '.[].name' 2>/dev/null | while read name; do
      if [ ! -d "/home/openclaw/evez-ecosystem/evezart-repos/$name" ]; then
        git clone --depth 1 "https://github.com/$org/$name.git" \
          "/home/openclaw/evez-ecosystem/evezart-repos/$name" 2>/dev/null
        echo "[$TS] 🆕 Discovered $org/$name" >> "$LOG"
      fi
    done
  done
fi

# ─── 4. SYNC — Push state to GitHub ───
if [ -d "/home/openclaw/evez-os/infra/.git" ]; then
  cd /home/openclaw/evez-os/infra
  cp /home/openclaw/MEMORY.md workspace-identity/ 2>/dev/null || true
  cp -r /home/openclaw/memory workspace-identity/ 2>/dev/null || true
  git add -A 2>/dev/null
  git diff --cached --quiet 2>/dev/null || \
    git commit -m "neuros-auto: $TS" 2>/dev/null
  git push origin main 2>/dev/null
  echo "[$TS] 📤 State synced" >> "$LOG"
fi

# ─── 5. CLEAN — Auto disk cleanup at 88% ───
USED=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$USED" -gt 88 ]; then
  echo "[$TS] 🧹 Disk at ${USED}% — cleaning" >> "$LOG"
  find /home/openclaw/evez-ecosystem/evezart-repos -name ".venv" -type d -exec rm -rf {} + 2>/dev/null
  find /home/openclaw/evez-ecosystem/evezart-repos -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null
  find /home/openclaw/evez-ecosystem/evezart-repos -name ".git" -type d -exec rm -rf {} + 2>/dev/null
  find /home/openclaw -name "*.log" -size +5M -delete 2>/dev/null
  pip cache purge 2>/dev/null
  npm cache clean --force 2>/dev/null
fi

echo "[$TS] 🧠 Autonomous cycle complete" >> "$LOG"
