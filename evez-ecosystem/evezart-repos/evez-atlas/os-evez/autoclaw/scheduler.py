"""autoclaw.scheduler — bounded loop runner (kill switch + disk guard + retention)."""
import time, os, json, shutil
from pathlib import Path
from evezos.spine import Spine

def get_cfg() -> dict:
    cfg_path = Path(os.environ.get("OG_DATA_DIR", "~/og_data")).expanduser() / "scheduler_config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text())
    return {"enabled": False, "interval_seconds": 600, "max_runs": 1000000, "max_disk_mb": 4096, "retention_runs": 80}

def disk_mb(path: Path) -> float:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / 1024 / 1024

def prune_old_runs(runs_dir: Path, keep: int):
    runs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    while len(runs) > keep:
        shutil.rmtree(runs.pop(0), ignore_errors=True)

def main():
    data_dir = Path(os.environ.get("OG_DATA_DIR", "~/og_data")).expanduser()
    spine = Spine(data_dir / "scheduler_spine.jsonl")
    print("[autoclaw] scheduler started")
    while True:
        cfg = get_cfg()
        stop_file = data_dir / "STOP"
        if stop_file.exists():
            print("[autoclaw] STOP file detected — halting")
            spine.append("stop", {"reason": "STOP file"})
            break
        if not cfg.get("enabled"):
            time.sleep(10)
            continue
        runs_dir = data_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        used_mb = disk_mb(data_dir)
        if used_mb > cfg.get("max_disk_mb", 4096):
            spine.append("disk_guard", {"used_mb": round(used_mb, 1), "limit_mb": cfg["max_disk_mb"]})
            print(f"[autoclaw] disk guard: {used_mb:.0f}MB > {cfg['max_disk_mb']}MB — pausing")
            time.sleep(60)
            continue
        # Prune
        prune_old_runs(runs_dir, cfg.get("retention_runs", 80))
        # Trigger build
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8080/runs/create", 
                data=b'{"seed":42,"steps":35}',
                timeout=30)
            spine.append("run_triggered", {"used_mb": round(used_mb, 1)})
            print(f"[autoclaw] run triggered (disk={used_mb:.0f}MB)")
        except Exception as e:
            spine.append("run_error", {"error": str(e)})
            print(f"[autoclaw] run error: {e}")
        time.sleep(cfg.get("interval_seconds", 600))

if __name__ == "__main__":
    main()
