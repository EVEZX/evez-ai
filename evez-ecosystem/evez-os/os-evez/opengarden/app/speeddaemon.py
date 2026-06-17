"""opengarden.app.speeddaemon — precomputes + caches maps/indexes."""
import time, os, json
from pathlib import Path
from evezos.spine import Spine

def main():
    data_dir = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
    spine = Spine(data_dir / "speeddaemon_spine.jsonl")
    runs_dir = data_dir / "runs"
    maps_dir = data_dir / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    print("[speeddaemon] started")
    while True:
        stop = data_dir / "STOP"
        if stop.exists():
            print("[speeddaemon] STOP")
            break
        runs = sorted([r.name for r in runs_dir.iterdir() if r.is_dir()], reverse=True) if runs_dir.exists() else []
        latest = {"runs": runs[:10], "count": len(runs), "updated": time.time()}
        (maps_dir / "latest.json").write_text(json.dumps(latest, indent=2))
        (maps_dir / "all.json").write_text(json.dumps({"runs": runs, "count": len(runs), "updated": time.time()}, indent=2))
        spine.append("maps_refreshed", {"count": len(runs)})
        time.sleep(30)

if __name__ == "__main__":
    main()
