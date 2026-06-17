#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/evezos"
RUNS="${ROOT}/runs"
NOW="$(date +%Y%m%d_%H%M%S)"
RUN_ID="ops_${NOW}"

echo "[1/5] Verify (latest)"
python -m evezos verify latest || true

echo "[2/5] Create run + generate spine"
python -m evezos init >/dev/null 2>&1 || true
python -m evezos play --seed 888 --steps 35 --run-id "${RUN_ID}"

echo "[3/5] Visualize + dashboards"
python -m evezos viz "${RUN_ID}"

echo "[4/5] Verify run"
python -m evezos verify "${RUN_ID}"

echo "[5/5] Export zip"
python -m evezos export --zip "${RUN_ID}"

echo "Open:"
echo "  ${RUNS}/${RUN_ID}/pimped_dashboard.html"
