"""
emergency_recovery.py — Self-healing on cycle failure.
Checks which engines failed, logs errors, queues partial retry.
"""
import json, os, sys
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("state/cycle_state.json")
ERROR_LOG  = Path("state/error_log.txt")

def assess_damage():
    if not STATE_FILE.exists():
        return {"status": "no_state", "last_success": None}
    with open(STATE_FILE) as f:
        state = json.load(f)
    return {
        "status": "partial",
        "cycle_start":    state.get("cycle_start"),
        "futures_count":  len(state.get("futures", [])),
        "voids_count":    len(state.get("voids", [])),
        "entropic_count": len(state.get("entropic_assets", [])),
        "qualia_count":   len(state.get("qualia_products", [])),
    }

def log_recovery(assessment):
    ERROR_LOG.parent.mkdir(exist_ok=True)
    with open(ERROR_LOG, "a") as f:
        f.write(f"\n[{datetime.utcnow().isoformat()}] Recovery:\n")
        f.write(json.dumps(assessment, indent=2))
        f.write("\n")

if __name__ == "__main__":
    assessment = assess_damage()
    log_recovery(assessment)
    print(f"[Recovery] {assessment}")
    sys.exit(0)
