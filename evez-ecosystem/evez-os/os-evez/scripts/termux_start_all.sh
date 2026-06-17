#!/usr/bin/env bash
# OS-EVEZ: Start All Compartments
# tmux session: redis | api | worker | scheduler | speeddaemon | autoclaw
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$HOME/.os_evez_env"
[ -f "$ENV_FILE" ] && source "$ENV_FILE"

export OG_DATA_DIR="${OG_DATA_DIR:-$HOME/og_data}"
export OG_REDIS_URL="${OG_REDIS_URL:-redis://127.0.0.1:6379/0}"
export OG_SIGNING_MODE="${OG_SIGNING_MODE:-ed25519}"
export OG_CREATOR_NAME="${OG_CREATOR_NAME:-Steven Crawford-Maggard}"
export OG_CREATOR_HANDLE="${OG_CREATOR_HANDLE:-EVEZ666}"
export OG_CREATOR_REPO="${OG_CREATOR_REPO:-github.com/EvezArt/evez-os}"
export OG_LICENSE_ID="${OG_LICENSE_ID:-AGPL-3.0}"
export OG_FREE_LAG_RUNS="${OG_FREE_LAG_RUNS:-5}"

cd "$REPO_DIR"
source .venv/bin/activate 2>/dev/null || true

# Kill old session if exists
tmux kill-session -t og 2>/dev/null || true

tmux new-session -d -s og -x 220 -y 50

# Window 0: redis
tmux rename-window -t og:0 redis
tmux send-keys -t og:0 "redis-server --save '' --loglevel warning" C-m

# Window 1: api
tmux new-window -t og -n api
tmux send-keys -t og:api "cd $REPO_DIR && source .venv/bin/activate && uvicorn opengarden.app.main:app --host 127.0.0.1 --port 8080 --log-level info" C-m

# Window 2: worker
tmux new-window -t og -n worker
tmux send-keys -t og:worker "cd $REPO_DIR && source .venv/bin/activate && rq worker -u $OG_REDIS_URL default 2>/dev/null || echo 'rq not available, worker skipped'" C-m

# Window 3: scheduler
tmux new-window -t og -n scheduler
tmux send-keys -t og:scheduler "cd $REPO_DIR && source .venv/bin/activate && python -m autoclaw.scheduler" C-m

# Window 4: speeddaemon
tmux new-window -t og -n speeddaemon
tmux send-keys -t og:speeddaemon "cd $REPO_DIR && source .venv/bin/activate && python -m opengarden.app.speeddaemon" C-m

# Window 5: autoclaw
tmux new-window -t og -n autoclaw
tmux send-keys -t og:autoclaw "cd $REPO_DIR && source .venv/bin/activate && python -m autoclaw.runner" C-m

sleep 2
echo ""
echo "┌─────────────────────────────────────────────────────┐"
echo "│  OS-EVEZ is RUNNING                                 │"
echo "│                                                     │"
echo "│  ARCADE:      http://127.0.0.1:8080/arcade         │"
echo "│  EVENTS:      http://127.0.0.1:8080/events         │"
echo "│  MARKET:      http://127.0.0.1:8080/market         │"
echo "│  PUBLIC KEY:  http://127.0.0.1:8080/public-key.html│"
echo "│  MAPS:        http://127.0.0.1:8080/maps/latest    │"
echo "│  ASSETS:      http://127.0.0.1:8080/assets/map.html│"
echo "│                                                     │"
echo "│  Creator: Steven Crawford-Maggard (EVEZ666)        │"
echo "│  github.com/EvezArt/evez-os                        │"
echo "└─────────────────────────────────────────────────────┘"
echo ""
echo "  tmux attach -t og      (to watch all windows)"
echo "  Ctrl+b d                (to detach)"
echo ""
echo "  STOP:  touch $OG_DATA_DIR/STOP"
echo ""
tmux attach -t og
