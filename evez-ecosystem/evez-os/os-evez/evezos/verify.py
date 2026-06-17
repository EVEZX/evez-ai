"""evezos.verify — full run verification (chain + manifest + signature)."""
import json
from pathlib import Path
from .replay import replay
from .manifest import verify_manifest


def verify_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    result = {"run_id": run_dir.name, "checks": {}}

    # Chain
    spine_path = run_dir / "spine.jsonl"
    chain_ok, chain_msg, _ = replay(spine_path) if spine_path.exists() else (False, "spine.jsonl missing", [])
    result["checks"]["chain"] = {"ok": chain_ok, "msg": chain_msg}

    # Manifest
    mf_ok, mf_msg = verify_manifest(run_dir)
    result["checks"]["manifest"] = {"ok": mf_ok, "msg": mf_msg}

    # Provenance
    prov = run_dir / "provenance" / "bundle_manifest.json"
    result["checks"]["provenance"] = {"ok": prov.exists(), "msg": "present" if prov.exists() else "missing"}

    result["ok"] = all(c["ok"] for c in result["checks"].values())
    return result
