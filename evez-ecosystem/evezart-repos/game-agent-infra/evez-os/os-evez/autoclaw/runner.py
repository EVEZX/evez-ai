"""autoclaw.runner — AutoClaw task runner (ingest → build → seal → export → refresh)."""
import time, os, json
from pathlib import Path
from evezos.spine import Spine

def main():
    data_dir = Path(os.environ.get("OG_DATA_DIR", "~/og_data")).expanduser()
    spine = Spine(data_dir / "autoclaw_spine.jsonl")
    print("[autoclaw.runner] started")
    while True:
        stop_file = data_dir / "STOP"
        if stop_file.exists():
            print("[autoclaw.runner] STOP")
            break
        spine.append("heartbeat", {"ts": time.time()})
        time.sleep(60)

if __name__ == "__main__":
    main()
