"""OS-EVEZ acceptance tests."""
import json, sys, os, tempfile, hashlib
from pathlib import Path

# Adjust path for test runner
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evezos.spine import Spine, _chain_hash
from evezos.manifest import build_manifest, verify_manifest
from evezos.object_store import ObjectStore, Node
from evezos.replay import replay


def test_canonical_json_hash():
    """Canonical JSON hashing is deterministic."""
    event = {"type": "test", "data": {"x": 1}}
    h1 = _chain_hash("0" * 64, event)
    h2 = _chain_hash("0" * 64, event)
    assert h1 == h2, "hash must be deterministic"
    assert len(h1) == 64, "sha256 hex = 64 chars"
    print("PASS test_canonical_json_hash")


def test_spine_append_and_chain():
    """Spine appends events with valid chain hashes."""
    with tempfile.TemporaryDirectory() as td:
        sp = Spine(Path(td) / "test.jsonl")
        e1 = sp.append("event_a", {"val": 1})
        e2 = sp.append("event_b", {"val": 2})
        events = sp.read_all()
        assert len(events) == 2
        # Verify chain
        ok, msg, _ = replay(Path(td) / "test.jsonl")
        assert ok, f"replay failed: {msg}"
        print("PASS test_spine_append_and_chain")


def test_manifest_verify():
    """Manifest build + verify round-trip."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_test"
        run_dir.mkdir()
        sp = Spine(run_dir / "spine.jsonl")
        for i in range(5):
            sp.append("step", {"i": i})
        (run_dir / "index.html").write_text("<html>test</html>")
        events = sp.read_all()
        mf = build_manifest("run_test", run_dir, events)
        import json
        (run_dir / "manifest.json").write_text(json.dumps(mf))
        ok, msg = verify_manifest(run_dir)
        assert ok, f"verify failed: {msg}"
        print("PASS test_manifest_verify")


def test_replay_determinism():
    """Replay produces same result on second call."""
    with tempfile.TemporaryDirectory() as td:
        sp = Spine(Path(td) / "r.jsonl")
        for i in range(10):
            sp.append("tick", {"i": i})
        ok1, msg1, evts1 = replay(Path(td) / "r.jsonl")
        ok2, msg2, evts2 = replay(Path(td) / "r.jsonl")
        assert ok1 and ok2
        assert [e["chain_hash"] for e in evts1] == [e["chain_hash"] for e in evts2]
        print("PASS test_replay_determinism")


def test_object_store():
    """Object store projection is deterministic."""
    store = ObjectStore()
    store.upsert(Node("run", "r1", {"status": "done"}))
    store.upsert(Node("run", "r2", {"status": "running"}))
    proj1 = store.project()
    proj2 = store.project()
    assert proj1 == proj2
    sha1 = store.store_sha()
    sha2 = store.store_sha()
    assert sha1 == sha2
    print("PASS test_object_store")


def test_scope_enforcement():
    """OpenClaw policy denies out-of-scope paths."""
    from openclaw.policy import load_policy, assert_fs_read, assert_fs_write
    policy = load_policy()
    assert assert_fs_read(policy, "./runs/test") is True
    assert assert_fs_read(policy, "/etc/passwd") is False
    assert assert_fs_write(policy, "./state/x") is True
    assert assert_fs_write(policy, "/tmp/evil") is False
    print("PASS test_scope_enforcement")


if __name__ == "__main__":
    test_canonical_json_hash()
    test_spine_append_and_chain()
    test_manifest_verify()
    test_replay_determinism()
    test_object_store()
    test_scope_enforcement()
    print()
    print("ALL TESTS PASSED")
