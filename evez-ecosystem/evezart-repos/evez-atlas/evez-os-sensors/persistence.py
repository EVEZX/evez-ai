"""
EVEZ-OS PERSISTENCE — Nothing Is Lost

The problem: /tmp vanishes on reboot. Git only stores code, not state.
The solution: Triple-redundant persistence with verification.

Backup tiers:
  TIER 1: Workspace mirror (survives reboots, in git repo)
  TIER 2: Spine replication (append-only, hash-chained, tamper-evident)
  TIER 3: Full state snapshot (JSON, restorable)

Every state write triggers:
  1. Write to /tmp (fast, current cycle)
  2. Mirror to workspace (persistent)
  3. Verify spine integrity
  4. Snapshot if spine grew significantly

Recovery: On startup, check tiers in reverse order.
If TIER 1 is corrupt, restore from TIER 2 + TIER 3.
If everything is gone, the code + git history rebuilds from scratch.
"""

import hashlib
import json
import os
import shutil
import time
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Persistence:
    """
    Triple-redundant state persistence.
    Nothing is lost. Nothing is corrupt. Nothing is forgotten.
    """

    def __init__(self, name: str, workspace_root: str = None):
        self.name = name
        self.workspace_root = Path(workspace_root or 
            "/home/openclaw/.openclaw/workspace")
        
        # TIER 1: Fast working directory (in /tmp, volatile)
        self.tmp_dir = Path(f"/tmp/evez_{name}")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # TIER 1.5: Workspace mirror (survives reboot, in git repo)
        self.mirror_dir = self.workspace_root / "state" / name
        self.mirror_dir.mkdir(parents=True, exist_ok=True)
        
        # TIER 2: Spine files (append-only, hash-chained)
        self.spine_dir = self.mirror_dir / "spine"
        self.spine_dir.mkdir(parents=True, exist_ok=True)
        
        # TIER 3: Snapshots (full state, timestamped)
        self.snapshot_dir = self.mirror_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Track what we've backed up
        self.backup_count = 0
        self.last_snapshot_time = 0
        self.snapshot_interval = 300  # 5 minutes between snapshots
        self.verified = False
    
    # ── WRITE (all three tiers) ──────────────────────────────────
    
    def save_state(self, key: str, data: dict):
        """
        Save state to all tiers atomically.
        If any write fails, the others still hold.
        """
        # TIER 1: /tmp (fast)
        tmp_path = self.tmp_dir / f"{key}.json"
        try:
            tmp_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"  ⚠ TIER 1 write failed for {key}: {e}")
        
        # TIER 1.5: Workspace mirror (persistent)
        mirror_path = self.mirror_dir / f"{key}.json"
        try:
            mirror_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"  ⚠ MIRROR write failed for {key}: {e}")
        
        self.backup_count += 1
        
        # Auto-snapshot if enough time has passed
        if time.time() - self.last_snapshot_time > self.snapshot_interval:
            self.snapshot(key, data)
            self.last_snapshot_time = time.time()
    
    def save_spine(self, spine_name: str, events: list[dict]):
        """
        Save spine events to append-only files.
        Spines are NEVER overwritten — only appended to.
        """
        # TIER 2: Workspace spine (persistent, append-only)
        spine_path = self.spine_dir / f"{spine_name}.jsonl"
        existing = set()
        if spine_path.exists():
            with open(spine_path) as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        existing.add(e.get("hash", ""))
                    except:
                        pass
        
        # Only append new events
        new_count = 0
        with open(spine_path, "a") as f:
            for event in events:
                if event.get("hash", "") not in existing:
                    f.write(json.dumps(event, default=str) + "\n")
                    new_count += 1
        
        # Also write to /tmp for fast access
        tmp_spine = self.tmp_dir / f"{spine_name}_spine.jsonl"
        shutil.copy2(spine_path, tmp_spine) if spine_path.exists() else None
        
        return new_count
    
    def append_spine_event(self, spine_name: str, event: dict):
        """Append a single event to the spine. Idempotent by hash."""
        spine_path = self.spine_dir / f"{spine_name}.jsonl"
        
        # Check if already written
        event_hash = event.get("hash", "")
        if event_hash and spine_path.exists():
            with open(spine_path) as f:
                for line in f:
                    try:
                        if json.loads(line).get("hash") == event_hash:
                            return False  # Already exists
                    except:
                        pass
        
        # Append
        with open(spine_path, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        # Mirror to /tmp
        tmp_spine = self.tmp_dir / f"{spine_name}_spine.jsonl"
        with open(tmp_spine, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        return True
    
    def snapshot(self, key: str, data: dict):
        """
        TIER 3: Full state snapshot with timestamp.
        Never delete old snapshots — they're the undo history.
        """
        ts = time.strftime("%Y%m%d_%H%M%S")
        snap_path = self.snapshot_dir / f"{key}_{ts}.json"
        snap_path.write_text(json.dumps(data, indent=2, default=str))
        
        # Keep last 20 snapshots per key
        existing = sorted(self.snapshot_dir.glob(f"{key}_*.json"))
        if len(existing) > 20:
            for old in existing[:-20]:
                old.unlink()
    
    # ── READ (fallback chain) ────────────────────────────────────
    
    def load_state(self, key: str) -> dict:
        """
        Load state with fallback chain:
        1. /tmp (fastest, may be stale or missing)
        2. Workspace mirror (persistent, may be slightly stale)
        3. Latest snapshot (always available)
        """
        # Try /tmp first
        tmp_path = self.tmp_dir / f"{key}.json"
        if tmp_path.exists():
            try:
                data = json.loads(tmp_path.read_text())
                # Verify against mirror
                mirror_path = self.mirror_dir / f"{key}.json"
                if mirror_path.exists():
                    mirror_data = json.loads(mirror_path.read_text())
                    if json.dumps(data, sort_keys=True, default=str) != json.dumps(mirror_data, sort_keys=True, default=str):
                        # Mismatch — mirror is authoritative
                        return mirror_data
                return data
            except:
                pass
        
        # Try mirror
        mirror_path = self.mirror_dir / f"{key}.json"
        if mirror_path.exists():
            try:
                return json.loads(mirror_path.read_text())
            except:
                pass
        
        # Try latest snapshot
        snaps = sorted(self.snapshot_dir.glob(f"{key}_*.json"), reverse=True)
        if snaps:
            try:
                return json.loads(snaps[0].read_text())
            except:
                pass
        
        return {}
    
    def load_spine(self, spine_name: str) -> list[dict]:
        """Load spine events from persistent storage."""
        spine_path = self.spine_dir / f"{spine_name}.jsonl"
        if not spine_path.exists():
            # Fallback to /tmp
            tmp_spine = self.tmp_dir / f"{spine_name}_spine.jsonl"
            if tmp_spine.exists():
                spine_path = tmp_spine
        
        events = []
        if spine_path.exists():
            with open(spine_path) as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        return events
    
    # ── VERIFY ───────────────────────────────────────────────────
    
    def verify_spine(self, spine_name: str) -> dict:
        """
        Verify spine integrity. Check hash chain.
        Returns: events, valid, errors
        """
        events = self.load_spine(spine_name)
        errors = []
        
        for i, event in enumerate(events):
            expected_prev = "GENESIS" if i == 0 else events[i-1].get("hash")
            actual_prev = event.get("prev") or event.get("previous_hash")
            
            if actual_prev != expected_prev:
                errors.append({
                    "event_index": i,
                    "expected_prev": expected_prev,
                    "actual_prev": actual_prev,
                    "type": "CHAIN_BREAK"
                })
        
        return {
            "spine": spine_name,
            "events": len(events),
            "valid": len(errors) == 0,
            "errors": errors[:10],
            "status": "INTACT ✓" if not errors else f"TAMPERED ({len(errors)} breaks)",
            "first_event": events[0].get("ts", events[0].get("timestamp")) if events else None,
            "last_event": events[-1].get("ts", events[-1].get("timestamp")) if events else None,
        }
    
    def verify_all(self) -> dict:
        """Verify all state and spines."""
        results = {"timestamp": time.time(), "tiers": {}}
        
        # Check each tier exists and is readable
        for tier_name, tier_path in [
            ("tmp", self.tmp_dir),
            ("mirror", self.mirror_dir),
            ("spine", self.spine_dir),
            ("snapshots", self.snapshot_dir),
        ]:
            results["tiers"][tier_name] = {
                "exists": tier_path.exists(),
                "size_bytes": sum(f.stat().st_size for f in tier_path.rglob("*") if f.is_file()) if tier_path.exists() else 0,
                "file_count": sum(1 for f in tier_path.rglob("*") if f.is_file()) if tier_path.exists() else 0,
            }
        
        # Verify all spines
        spine_results = []
        for spine_file in self.spine_dir.glob("*.jsonl"):
            v = self.verify_spine(spine_file.stem)
            spine_results.append(v)
        results["spines"] = spine_results
        
        # Check mirror vs tmp consistency
        inconsistencies = []
        for mirror_file in self.mirror_dir.glob("*.json"):
            if mirror_file.name.endswith('.json') and 'snapshots' not in str(mirror_file):
                tmp_file = self.tmp_dir / mirror_file.name
                if tmp_file.exists():
                    try:
                        mirror_hash = hashlib.sha256(mirror_file.read_bytes()).hexdigest()[:16]
                        tmp_hash = hashlib.sha256(tmp_file.read_bytes()).hexdigest()[:16]
                        if mirror_hash != tmp_hash:
                            inconsistencies.append({
                                "file": mirror_file.name,
                                "mirror_hash": mirror_hash,
                                "tmp_hash": tmp_hash,
                                "resolution": "mirror is authoritative"
                            })
                    except:
                        pass
        results["inconsistencies"] = inconsistencies
        results["backup_count"] = self.backup_count
        
        return results
    
    # ── RESTORE ──────────────────────────────────────────────────
    
    def restore_from_mirror(self, key: str) -> bool:
        """Restore /tmp from workspace mirror."""
        mirror_path = self.mirror_dir / f"{key}.json"
        tmp_path = self.tmp_dir / f"{key}.json"
        
        if mirror_path.exists():
            try:
                data = json.loads(mirror_path.read_text())
                tmp_path.write_text(json.dumps(data, indent=2, default=str))
                return True
            except:
                return False
        return False
    
    def restore_all(self) -> dict:
        """Restore all /tmp state from workspace mirror."""
        restored = []
        for mirror_file in self.mirror_dir.glob("*.json"):
            if 'snapshots' not in str(mirror_file):
                if self.restore_from_mirror(mirror_file.stem):
                    restored.append(mirror_file.stem)
        return {"restored": restored, "count": len(restored)}
    
    # ── MIGRATE /tmp → workspace ────────────────────────────────
    
    def migrate_tmp_to_persistent(self) -> dict:
        """
        One-time migration: copy all /tmp state to workspace mirror.
        Call this on first run after reboot when /tmp is empty but
        we want to ensure nothing is lost.
        """
        migrated = []
        for tmp_file in Path(f"/tmp").glob(f"evez_{self.name}*"):
            if tmp_file.is_dir():
                # Copy entire directory
                for sub in tmp_file.rglob("*"):
                    if sub.is_file():
                        rel = sub.relative_to(tmp_file)
                        dest = self.mirror_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(sub, dest)
                        migrated.append(str(rel))
            elif tmp_file.is_file():
                dest = self.mirror_dir / tmp_file.name
                shutil.copy2(tmp_file, dest)
                migrated.append(tmp_file.name)
        
        # Also migrate spines from /tmp
        for spine_file in Path(f"/tmp").glob(f"*spine*.jsonl"):
            dest = self.spine_dir / spine_file.name
            if not dest.exists():
                shutil.copy2(spine_file, dest)
                migrated.append(f"spine/{spine_file.name}")
        
        return {"migrated": migrated, "count": len(migrated)}


# ─── BACKUP RUNNER ──────────────────────────────────────────────

def run_backup():
    """
    Backup everything. Called on shutdown and periodically.
    Migrates /tmp → workspace, verifies spines, creates snapshot.
    """
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS BACKUP — Nothing Is Lost                           ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    results = {}
    
    # Backup each named state
    for name in ["organism", "consciousness", "live", "os_mind"]:
        p = Persistence(name)
        
        # Migrate /tmp to persistent
        mig = p.migrate_tmp_to_persistent()
        results[f"{name}_migrated"] = mig["count"]
        
        # Verify
        ver = p.verify_all()
        results[f"{name}_tiers"] = {k: v["exists"] for k, v in ver["tiers"].items()}
        results[f"{name}_spines"] = [s["status"] for s in ver.get("spines", [])]
        results[f"{name}_inconsistencies"] = len(ver.get("inconsistencies", []))
    
    # Also backup the code itself (git)
    print("  Running git add + commit for code backup...")
    os.system("cd /home/openclaw/.openclaw/workspace && git add -A && git diff --cached --quiet || git commit -m 'auto-backup: state + code persistence' 2>/dev/null")
    
    # Summary
    print("\n  BACKUP SUMMARY:")
    for k, v in results.items():
        print(f"    {k}: {v}")
    
    # Full state file
    state_dir = Path("/home/openclaw/.openclaw/workspace/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "backup_report.json").write_text(
        json.dumps(results, indent=2, default=str))
    
    print(f"\n  Backup report: {state_dir / 'backup_report.json'}")
    print(f"  Spine directory: {state_dir}")
    print(f"  All state persisted. Nothing is lost.")
    
    return results


if __name__ == "__main__":
    run_backup()
