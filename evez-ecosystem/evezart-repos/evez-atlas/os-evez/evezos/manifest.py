"""evezos.manifest — sealed run manifest builder + verifier."""
import hashlib, json, time
from pathlib import Path
from .spine import _chain_hash


def build_manifest(run_id: str, run_dir: Path, spine_events: list) -> dict:
    root_hash = "0" * 64
    for evt in spine_events:
        root_hash = _chain_hash(root_hash, evt)
    manifest = {
        "run_id": run_id,
        "created_at": time.time(),
        "spine_events": len(spine_events),
        "root_hash": root_hash,
        "files": {},
    }
    for f in sorted(run_dir.rglob("*")):
        if f.is_file() and f.name != "manifest.json":
            rel = str(f.relative_to(run_dir))
            manifest["files"][rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return manifest


def verify_manifest(run_dir: Path) -> tuple[bool, str]:
    mf_path = run_dir / "manifest.json"
    if not mf_path.exists():
        return False, "manifest.json missing"
    mf = json.loads(mf_path.read_text())
    for rel_path, expected_sha in mf.get("files", {}).items():
        fp = run_dir / rel_path
        if not fp.exists():
            return False, f"missing file: {rel_path}"
        actual = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual != expected_sha:
            return False, f"hash mismatch: {rel_path}"
    return True, "OK"
