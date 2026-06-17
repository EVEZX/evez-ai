#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# EVEZ-OS EVOLVE — Self-evolution loop
# Runs every 30 min. Pulls updates, discovers repos, self-heals, pushes state.
# ═══════════════════════════════════════════════════════════════
set -euo pipefail
EVOLVE_DIR="${EVEZ_HOME:-$HOME}/evez-os"
LOG="/tmp/evez-evolve.log"
TS=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "[$TS] 🧬 Evolution cycle start" >> "$LOG"

# ─── Pull Latest Code ───
for repo in evez-os infra; do
  if [ -d "$EVOLVE_DIR/$repo/.git" ]; then
    cd "$EVOLVE_DIR/$repo"
    git pull --ff-only 2>/dev/null && \
      echo "[$TS] ✅ Pulled $repo" >> "$LOG" || \
      echo "[$TS] ⚠️ $repo up to date" >> "$LOG"
  fi
done

# ─── Self-Heal: Restart Any Down Services ───
for svc in openclaw-gateway evez-provider evez-omega evez-filter evez-services-hub; do
  if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
    : # healthy
  else
    systemctl --user restart "$svc" 2>/dev/null
    echo "[$TS] 🔧 Restarted $svc" >> "$LOG"
  fi
done

# ─── Auto-Discover New Repos ───
if command -v gh &>/dev/null; then
  CLONED_DIR="$EVOLVE_DIR/evezart-repos"
  mkdir -p "$CLONED_DIR"
  for org in EvezArt EVEZX; do
    gh api "/users/$org/repos?per_page=100" --jq '.[].name' 2>/dev/null | while read name; do
      if [ ! -d "$CLONED_DIR/$name" ]; then
        git clone --depth 1 "https://github.com/$org/$name.git" "$CLONED_DIR/$name" 2>/dev/null
        echo "[$TS] 🆕 Discovered $org/$name" >> "$LOG"
      fi
    done
  done
fi

# ─── Push State to GitHub ───
if [ -d "$EVOLVE_DIR/infra/.git" ]; then
  cd "$EVOLVE_DIR/infra"
  cp "$HOME/MEMORY.md" workspace-identity/ 2>/dev/null || true
  cp -r "$HOME/memory" workspace-identity/ 2>/dev/null || true
  git add -A 2>/dev/null
  git diff --cached --quiet 2>/dev/null || \
    git commit -m "auto-evolve: $TS" 2>/dev/null
  git push origin main 2>/dev/null
  echo "[$TS] 📤 State pushed" >> "$LOG"
fi

# ─── Clean Up Old Data ───
find /tmp -name "*.log" -mtime +7 -delete 2>/dev/null
find "$EVOLVE_DIR/evezart-repos" -name ".git" -type d -exec rm -rf {} + 2>/dev/null
# Remove APKs and other large binaries
find "$EVOLVE_DIR" -name "*.apk" -delete 2>/dev/null

echo "[$TS] 🧬 Evolution cycle complete" >> "$LOG"
