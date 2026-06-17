"""Extended test coverage for os-evez.

Covers modules NOT tested in test_core.py:
  - evezos.verify   (verify_run)
  - evezos.viz      (summarize_spine)
  - evezos.spine    (edge-cases: empty read, resume from existing file)
  - evezos.object_store (edge-cases: get, upsert-update, empty store sha)
  - openclaw.policy (check_kill_switch, assert_shell, load_policy from file)
  - openclaw.tools  (ToolRunner: read, write, shell, budget, kill-switch)
  - openplanter.dag (DAG: add_job, ready_jobs, mark state transitions)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Make sure the package root is on the path regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evezos.spine import Spine, _chain_hash
from evezos.replay import replay
from evezos.manifest import build_manifest, verify_manifest
from evezos.object_store import ObjectStore, Node
from evezos.verify import verify_run
from evezos.viz import summarize_spine
from openclaw.policy import (
    DEFAULT_POLICY,
    load_policy,
    check_kill_switch,
    assert_fs_read,
    assert_fs_write,
    assert_shell,
)
from openclaw.tools import ToolRunner
from openplanter.dag import DAG, Job


# ---------------------------------------------------------------------------
# evezos.spine  — edge cases
# ---------------------------------------------------------------------------

def test_spine_read_all_nonexistent():
    """read_all on a path that doesn't exist returns empty list."""
    spine = Spine(Path("/tmp/_nonexistent_spine_xyz.jsonl"))
    # The Spine constructor creates parent dirs but won't create the file itself
    # unless appended to. We never append, so file should not exist.
    if not Path("/tmp/_nonexistent_spine_xyz.jsonl").exists():
        result = spine.read_all()
        assert result == [], f"Expected [], got {result}"
    print("PASS test_spine_read_all_nonexistent")


def test_spine_resume_existing():
    """A new Spine opened on an existing file resumes from the last hash."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "resume.jsonl"
        # First session: write two events
        sp1 = Spine(path)
        e1 = sp1.append("alpha", {"n": 1})
        e2 = sp1.append("beta", {"n": 2})
        last_hash = e2["chain_hash"]

        # Second session: open same file, append one more
        sp2 = Spine(path)
        e3 = sp2.append("gamma", {"n": 3})

        # Chain must validate across both sessions
        ok, msg, events = replay(path)
        assert ok, f"replay after resume failed: {msg}"
        assert len(events) == 3
        # Verify the internal state was correctly restored
        assert sp2._prev_hash == e3["chain_hash"], "prev_hash not updated after append"
    print("PASS test_spine_resume_existing")


def test_spine_chain_hash_different_events():
    """Different events produce different hashes."""
    h1 = _chain_hash("0" * 64, {"type": "a"})
    h2 = _chain_hash("0" * 64, {"type": "b"})
    assert h1 != h2, "distinct events must yield distinct hashes"
    print("PASS test_spine_chain_hash_different_events")


def test_spine_chain_hash_prev_matters():
    """Different prev hashes produce different chain hashes for same event."""
    event = {"type": "same"}
    h1 = _chain_hash("0" * 64, event)
    h2 = _chain_hash("1" * 64, event)
    assert h1 != h2, "changing prev_hash must change chain_hash"
    print("PASS test_spine_chain_hash_prev_matters")


# ---------------------------------------------------------------------------
# evezos.replay  — edge cases
# ---------------------------------------------------------------------------

def test_replay_empty_spine():
    """replay() on an empty (non-existent) spine returns ok=True, empty list."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "empty.jsonl"
        ok, msg, events = replay(path)
        assert ok, f"expected ok=True for empty spine, got msg={msg}"
        assert events == []
    print("PASS test_replay_empty_spine")


def test_replay_detects_tampered_hash():
    """replay() returns ok=False when chain hash is manually corrupted."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "tampered.jsonl"
        sp = Spine(path)
        sp.append("good", {"v": 1})
        sp.append("good", {"v": 2})

        # Tamper: read lines, corrupt the first event's hash
        lines = path.read_text().splitlines()
        first = json.loads(lines[0])
        first["chain_hash"] = "deadbeef" * 8  # 64 hex chars of garbage
        lines[0] = json.dumps(first)
        path.write_text("\n".join(lines) + "\n")

        ok, msg, _ = replay(path)
        assert not ok, "tampered chain should fail replay"
        assert "chain break" in msg
    print("PASS test_replay_detects_tampered_hash")


# ---------------------------------------------------------------------------
# evezos.verify  — verify_run
# ---------------------------------------------------------------------------

def test_verify_run_all_ok():
    """verify_run returns ok=True when spine, manifest and provenance are present."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_ok"
        run_dir.mkdir()

        # Write spine
        sp = Spine(run_dir / "spine.jsonl")
        for i in range(3):
            sp.append("step", {"i": i})
        events = sp.read_all()

        # Write a dummy file and build manifest
        (run_dir / "index.html").write_text("<html/>")
        mf = build_manifest("run_ok", run_dir, events)
        (run_dir / "manifest.json").write_text(json.dumps(mf))

        # Write provenance
        prov_dir = run_dir / "provenance"
        prov_dir.mkdir()
        (prov_dir / "bundle_manifest.json").write_text(json.dumps({"ok": True}))

        result = verify_run(run_dir)
        assert result["ok"], f"verify_run should pass, got: {result}"
        assert result["checks"]["chain"]["ok"]
        assert result["checks"]["manifest"]["ok"]
        assert result["checks"]["provenance"]["ok"]
    print("PASS test_verify_run_all_ok")


def test_verify_run_missing_spine():
    """verify_run reports chain failure when spine.jsonl is absent."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_no_spine"
        run_dir.mkdir()
        # No spine; create a dummy manifest so the manifest check passes
        (run_dir / "manifest.json").write_text(json.dumps({"files": {}}))

        result = verify_run(run_dir)
        # Chain check must fail (spine missing)
        assert not result["checks"]["chain"]["ok"], "chain should fail without spine"
        assert not result["ok"], "overall result should be False"
    print("PASS test_verify_run_missing_spine")


def test_verify_run_missing_manifest():
    """verify_run reports manifest failure when manifest.json is absent."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_no_manifest"
        run_dir.mkdir()
        sp = Spine(run_dir / "spine.jsonl")
        sp.append("step", {"i": 0})

        result = verify_run(run_dir)
        assert not result["checks"]["manifest"]["ok"], "manifest check should fail"
        assert not result["ok"]
    print("PASS test_verify_run_missing_manifest")


def test_verify_run_missing_provenance():
    """verify_run reports provenance failure when bundle_manifest.json is absent."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_no_prov"
        run_dir.mkdir()

        sp = Spine(run_dir / "spine.jsonl")
        sp.append("step", {"i": 0})
        events = sp.read_all()
        mf = build_manifest("run_no_prov", run_dir, events)
        (run_dir / "manifest.json").write_text(json.dumps(mf))

        result = verify_run(run_dir)
        assert not result["checks"]["provenance"]["ok"], "provenance check should fail"
        assert not result["ok"]
    print("PASS test_verify_run_missing_provenance")


# ---------------------------------------------------------------------------
# evezos.viz  — summarize_spine
# ---------------------------------------------------------------------------

def test_summarize_spine_nonexistent():
    """summarize_spine returns a 'not found' message for missing file."""
    msg = summarize_spine(Path("/tmp/_no_such_spine_abc.jsonl"))
    assert "not found" in msg.lower(), f"Expected 'not found' in: {msg!r}"
    print("PASS test_summarize_spine_nonexistent")


def test_summarize_spine_with_events():
    """summarize_spine returns a header line and at most 10 event lines."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "viz.jsonl"
        sp = Spine(path)
        for i in range(15):
            sp.append("tick", {"i": i})

        summary = summarize_spine(path)
        lines = summary.splitlines()
        # First line is the header
        assert "15 events" in lines[0], f"Header should show event count: {lines[0]}"
        # Body lines: at most 10 (the last 10 events)
        body = [l for l in lines[1:] if l.strip()]
        assert len(body) <= 10, f"Expected at most 10 event lines, got {len(body)}"
    print("PASS test_summarize_spine_with_events")


def test_summarize_spine_single_event():
    """summarize_spine works correctly with exactly one event."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "single.jsonl"
        sp = Spine(path)
        sp.append("solo", {"x": 42})
        summary = summarize_spine(path)
        assert "1 events" in summary
        assert "solo" in summary
    print("PASS test_summarize_spine_single_event")


# ---------------------------------------------------------------------------
# evezos.object_store  — edge cases
# ---------------------------------------------------------------------------

def test_object_store_get():
    """ObjectStore.get returns the correct node or None."""
    store = ObjectStore()
    node = Node("task", "t1", {"status": "pending"})
    store.upsert(node)
    assert store.get("t1") is node
    assert store.get("missing") is None
    print("PASS test_object_store_get")


def test_object_store_upsert_update():
    """upsert on same id replaces the node, and sha changes."""
    store = ObjectStore()
    store.upsert(Node("task", "t1", {"v": 1}))
    sha1 = store.store_sha()
    store.upsert(Node("task", "t1", {"v": 2}))
    sha2 = store.store_sha()
    assert sha1 != sha2, "SHA should change after updating a node"
    assert store.get("t1").attrs == {"v": 2}
    print("PASS test_object_store_upsert_update")


def test_object_store_empty_sha():
    """An empty store has a stable sha256."""
    store = ObjectStore()
    sha = store.store_sha()
    assert len(sha) == 64
    assert sha == store.store_sha(), "Empty store sha must be deterministic"
    print("PASS test_object_store_empty_sha")


def test_object_store_project_sorted():
    """project() returns nodes sorted by id."""
    store = ObjectStore()
    store.upsert(Node("run", "z_run", {}))
    store.upsert(Node("run", "a_run", {}))
    store.upsert(Node("run", "m_run", {}))
    proj = store.project()
    ids = [n["id"] for n in proj]
    assert ids == sorted(ids), f"project() must be sorted by id, got {ids}"
    print("PASS test_object_store_project_sorted")


def test_node_sha256_deterministic():
    """Node.sha256() is deterministic for the same attrs."""
    n = Node("event", "e1", {"val": 99, "tag": "test"})
    assert n.sha256() == n.sha256()
    # Different attrs → different hash
    n2 = Node("event", "e1", {"val": 100, "tag": "test"})
    assert n.sha256() != n2.sha256()
    print("PASS test_node_sha256_deterministic")


# ---------------------------------------------------------------------------
# openclaw.policy  — extended coverage
# ---------------------------------------------------------------------------

def test_policy_check_kill_switch_active():
    """check_kill_switch returns True when STOP file is present."""
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        (data_dir / "STOP").touch()
        assert check_kill_switch(DEFAULT_POLICY, data_dir) is True
    print("PASS test_policy_check_kill_switch_active")


def test_policy_check_kill_switch_inactive():
    """check_kill_switch returns False when STOP file is absent."""
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        assert check_kill_switch(DEFAULT_POLICY, data_dir) is False
    print("PASS test_policy_check_kill_switch_inactive")


def test_policy_assert_shell_allowed():
    """assert_shell allows commands in the allowlist."""
    policy = DEFAULT_POLICY
    assert assert_shell(policy, "ls -la") is True
    assert assert_shell(policy, "echo hello world") is True
    assert assert_shell(policy, "python script.py") is True
    print("PASS test_policy_assert_shell_allowed")


def test_policy_assert_shell_denied():
    """assert_shell denies commands not in the allowlist."""
    policy = DEFAULT_POLICY
    assert assert_shell(policy, "rm -rf /") is False
    assert assert_shell(policy, "curl http://evil.com") is False
    assert assert_shell(policy, "bash exploit.sh") is False
    print("PASS test_policy_assert_shell_denied")


def test_policy_assert_shell_empty_cmd():
    """assert_shell returns False for empty or whitespace-only commands."""
    policy = DEFAULT_POLICY
    assert assert_shell(policy, "") is False
    assert assert_shell(policy, "   ") is False
    print("PASS test_policy_assert_shell_empty_cmd")


def test_policy_load_from_file():
    """load_policy reads a YAML policy file when path exists."""
    import yaml

    custom = {
        "capabilities": {
            "FS_READ": {"allow_paths": ["./custom_data"]},
            "FS_WRITE": {"allow_paths": []},
            "SHELL": {"allow_commands": [], "workdir_jail": "."},
            "NET_OUT": {"enabled": False},
        },
        "kill_switch": {"stop_file": "./state/STOP"},
        "budgets": {},
    }
    with tempfile.TemporaryDirectory() as td:
        policy_path = Path(td) / "policy.yaml"
        policy_path.write_text(yaml.dump(custom))
        loaded = load_policy(policy_path)
        assert loaded["capabilities"]["FS_READ"]["allow_paths"] == ["./custom_data"]
    print("PASS test_policy_load_from_file")


def test_policy_load_default_when_file_missing():
    """load_policy falls back to DEFAULT_POLICY when file does not exist."""
    policy = load_policy(Path("/tmp/_no_policy_file_xyz.yaml"))
    assert policy == DEFAULT_POLICY
    print("PASS test_policy_load_default_when_file_missing")


def test_policy_assert_fs_read_exact_prefix():
    """assert_fs_read accepts paths that start with an allowed prefix."""
    policy = DEFAULT_POLICY
    assert assert_fs_read(policy, "./runs/my_run/spine.jsonl") is True
    assert assert_fs_read(policy, "./fixtures/sample.bin") is True
    assert assert_fs_read(policy, "./state/cfg.json") is True
    # Outside allow list
    assert assert_fs_read(policy, "/home/user/secret") is False
    assert assert_fs_read(policy, "../runs/escape") is False
    print("PASS test_policy_assert_fs_read_exact_prefix")


def test_policy_assert_fs_write_allowed_denied():
    """assert_fs_write only allows writes to ./runs and ./state."""
    policy = DEFAULT_POLICY
    assert assert_fs_write(policy, "./runs/output.txt") is True
    assert assert_fs_write(policy, "./state/flag") is True
    assert assert_fs_write(policy, "./fixtures/input.bin") is False
    assert assert_fs_write(policy, "/etc/hosts") is False
    print("PASS test_policy_assert_fs_write_allowed_denied")


# ---------------------------------------------------------------------------
# openclaw.tools  — ToolRunner
# ---------------------------------------------------------------------------

def test_tool_runner_read_allowed(tmp_path):
    """ToolRunner.read_file reads from allowed paths."""
    # Create a real file inside the allowed ./runs prefix
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    target = runs_dir / "data.txt"
    target.write_text("hello runner")

    runner = ToolRunner(data_dir=tmp_path)
    # Patch policy so the allow_paths cover our temp dir
    runner.policy["capabilities"]["FS_READ"]["allow_paths"] = [str(runs_dir)]
    content = runner.read_file(str(target))
    assert content == "hello runner"
    print("PASS test_tool_runner_read_allowed")


def test_tool_runner_read_denied(tmp_path):
    """ToolRunner.read_file raises PermissionError for disallowed paths."""
    runner = ToolRunner(data_dir=tmp_path)
    try:
        runner.read_file("/etc/passwd")
        assert False, "Expected PermissionError"
    except PermissionError as e:
        assert "FS_READ denied" in str(e)
    print("PASS test_tool_runner_read_denied")


def test_tool_runner_write_allowed(tmp_path):
    """ToolRunner.write_file writes to allowed paths."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    out_path = runs_dir / "output.txt"

    runner = ToolRunner(data_dir=tmp_path)
    runner.policy["capabilities"]["FS_WRITE"]["allow_paths"] = [str(runs_dir)]
    runner.write_file(str(out_path), "written!")
    assert out_path.read_text() == "written!"
    print("PASS test_tool_runner_write_allowed")


def test_tool_runner_write_denied(tmp_path):
    """ToolRunner.write_file raises PermissionError for disallowed paths."""
    runner = ToolRunner(data_dir=tmp_path)
    try:
        runner.write_file("/tmp/evil_file.txt", "bad")
        assert False, "Expected PermissionError"
    except PermissionError as e:
        assert "FS_WRITE denied" in str(e)
    print("PASS test_tool_runner_write_denied")


def test_tool_runner_shell_allowed(tmp_path):
    """ToolRunner.run_shell executes an allowed command and returns output."""
    runner = ToolRunner(data_dir=tmp_path)
    output = runner.run_shell("echo hello_from_shell")
    assert "hello_from_shell" in output
    print("PASS test_tool_runner_shell_allowed")


def test_tool_runner_shell_denied(tmp_path):
    """ToolRunner.run_shell raises PermissionError for disallowed commands."""
    runner = ToolRunner(data_dir=tmp_path)
    try:
        runner.run_shell("curl http://example.com")
        assert False, "Expected PermissionError"
    except PermissionError as e:
        assert "SHELL denied" in str(e)
    print("PASS test_tool_runner_shell_denied")


def test_tool_runner_budget_exceeded(tmp_path):
    """ToolRunner raises RuntimeError after the call budget is exhausted."""
    runner = ToolRunner(data_dir=tmp_path)
    runner.max_calls = 2

    runner.run_shell("echo one")
    runner.run_shell("echo two")
    try:
        runner.run_shell("echo three")
        assert False, "Expected RuntimeError for budget exceeded"
    except RuntimeError as e:
        assert "budget exceeded" in str(e).lower()
    print("PASS test_tool_runner_budget_exceeded")


def test_tool_runner_kill_switch(tmp_path):
    """ToolRunner raises RuntimeError when STOP file is present."""
    runner = ToolRunner(data_dir=tmp_path)
    (tmp_path / "STOP").touch()
    try:
        runner.run_shell("echo hi")
        assert False, "Expected RuntimeError for kill switch"
    except RuntimeError as e:
        assert "KILL SWITCH" in str(e)
    print("PASS test_tool_runner_kill_switch")


def test_tool_runner_call_count_increments(tmp_path):
    """call_count increments with each successful tool call."""
    runner = ToolRunner(data_dir=tmp_path)
    assert runner.call_count == 0
    runner.run_shell("echo a")
    assert runner.call_count == 1
    runner.run_shell("echo b")
    assert runner.call_count == 2
    print("PASS test_tool_runner_call_count_increments")


# ---------------------------------------------------------------------------
# openplanter.dag  — DAG / Job
# ---------------------------------------------------------------------------

def test_dag_add_and_ready():
    """A job with no dependencies is immediately ready."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        job = Job(id="j1", task="do_thing")
        dag.add_job(job)
        ready = dag.ready_jobs()
        assert len(ready) == 1 and ready[0].id == "j1"
    print("PASS test_dag_add_and_ready")


def test_dag_dependency_blocks_ready():
    """A job whose dependency is not done is NOT ready."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.add_job(Job(id="j1", task="first"))
        dag.add_job(Job(id="j2", task="second", depends_on=["j1"]))
        ready = dag.ready_jobs()
        ids = {j.id for j in ready}
        assert "j2" not in ids, "j2 should not be ready while j1 is pending"
        assert "j1" in ids
    print("PASS test_dag_dependency_blocks_ready")


def test_dag_dependency_unblocked_after_done():
    """After marking a dependency done, the dependent job becomes ready."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.add_job(Job(id="j1", task="first"))
        dag.add_job(Job(id="j2", task="second", depends_on=["j1"]))
        dag.mark("j1", "done")
        ready = dag.ready_jobs()
        ids = {j.id for j in ready}
        assert "j2" in ids, "j2 should be ready after j1 is done"
    print("PASS test_dag_dependency_unblocked_after_done")


def test_dag_mark_state_transitions():
    """mark() correctly updates job state and timestamps."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.add_job(Job(id="j1", task="work"))
        dag.mark("j1", "running")
        assert dag.jobs["j1"].state == "running"
        assert dag.jobs["j1"].started_at > 0
        dag.mark("j1", "done", result={"exit_code": 0})
        assert dag.jobs["j1"].state == "done"
        assert dag.jobs["j1"].finished_at > 0
        assert dag.jobs["j1"].result == {"exit_code": 0}
    print("PASS test_dag_mark_state_transitions")


def test_dag_mark_failed():
    """mark() with 'failed' sets finished_at and state correctly."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.add_job(Job(id="j1", task="risky"))
        dag.mark("j1", "running")
        dag.mark("j1", "failed", result={"error": "timeout"})
        assert dag.jobs["j1"].state == "failed"
        assert dag.jobs["j1"].finished_at > 0
    print("PASS test_dag_mark_failed")


def test_dag_mark_nonexistent_job_noop():
    """mark() on an unknown job id is a no-op (no crash)."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.mark("ghost", "done")  # should not raise
    print("PASS test_dag_mark_nonexistent_job_noop")


def test_dag_spine_written():
    """DAG writes job_added and job_state events to spine."""
    with tempfile.TemporaryDirectory() as td:
        spine_path = Path(td) / "dag_spine.jsonl"
        dag = DAG(spine_path)
        dag.add_job(Job(id="j1", task="work"))
        dag.mark("j1", "done")
        ok, msg, events = replay(spine_path)
        assert ok, f"DAG spine replay failed: {msg}"
        types = [e["type"] for e in events]
        assert "job_added" in types
        assert "job_state" in types
    print("PASS test_dag_spine_written")


def test_dag_no_ready_when_all_done():
    """ready_jobs() returns empty list when all jobs are done."""
    with tempfile.TemporaryDirectory() as td:
        dag = DAG(Path(td) / "dag.jsonl")
        dag.add_job(Job(id="j1", task="a"))
        dag.add_job(Job(id="j2", task="b", depends_on=["j1"]))
        dag.mark("j1", "done")
        dag.mark("j2", "done")
        assert dag.ready_jobs() == []
    print("PASS test_dag_no_ready_when_all_done")


# ---------------------------------------------------------------------------
# evezos.manifest  — edge cases not in test_core
# ---------------------------------------------------------------------------

def test_manifest_missing_file_fails_verify():
    """verify_manifest returns False when a listed file is deleted."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_missing"
        run_dir.mkdir()
        sp = Spine(run_dir / "spine.jsonl")
        sp.append("step", {"i": 0})
        (run_dir / "extra.txt").write_text("important")
        events = sp.read_all()
        mf = build_manifest("run_missing", run_dir, events)
        (run_dir / "manifest.json").write_text(json.dumps(mf))

        # Delete a tracked file after building manifest
        (run_dir / "extra.txt").unlink()
        ok, msg = verify_manifest(run_dir)
        assert not ok, "verify_manifest should fail when a file is missing"
        assert "missing file" in msg
    print("PASS test_manifest_missing_file_fails_verify")


def test_manifest_tampered_file_fails_verify():
    """verify_manifest returns False when a file's content is altered."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_tamper"
        run_dir.mkdir()
        sp = Spine(run_dir / "spine.jsonl")
        sp.append("step", {"i": 0})
        (run_dir / "data.bin").write_bytes(b"\x00" * 64)
        events = sp.read_all()
        mf = build_manifest("run_tamper", run_dir, events)
        (run_dir / "manifest.json").write_text(json.dumps(mf))

        # Tamper with the file
        (run_dir / "data.bin").write_bytes(b"\xff" * 64)
        ok, msg = verify_manifest(run_dir)
        assert not ok, "verify_manifest should fail after tampering"
        assert "hash mismatch" in msg
    print("PASS test_manifest_tampered_file_fails_verify")


def test_manifest_missing_manifest_json():
    """verify_manifest returns False when manifest.json does not exist."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_nomf"
        run_dir.mkdir()
        ok, msg = verify_manifest(run_dir)
        assert not ok
        assert "missing" in msg.lower()
    print("PASS test_manifest_missing_manifest_json")


def test_build_manifest_empty_spine():
    """build_manifest works with zero spine events."""
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / "run_empty"
        run_dir.mkdir()
        (run_dir / "note.txt").write_text("empty run")
        mf = build_manifest("run_empty", run_dir, [])
        assert mf["spine_events"] == 0
        assert "note.txt" in mf["files"]
        assert len(mf["root_hash"]) == 64
    print("PASS test_build_manifest_empty_spine")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # evezos.spine edge cases
    test_spine_read_all_nonexistent()
    test_spine_resume_existing()
    test_spine_chain_hash_different_events()
    test_spine_chain_hash_prev_matters()

    # evezos.replay edge cases
    test_replay_empty_spine()
    test_replay_detects_tampered_hash()

    # evezos.verify
    test_verify_run_all_ok()
    test_verify_run_missing_spine()
    test_verify_run_missing_manifest()
    test_verify_run_missing_provenance()

    # evezos.viz
    test_summarize_spine_nonexistent()
    test_summarize_spine_with_events()
    test_summarize_spine_single_event()

    # evezos.object_store edge cases
    test_object_store_get()
    test_object_store_upsert_update()
    test_object_store_empty_sha()
    test_object_store_project_sorted()
    test_node_sha256_deterministic()

    # openclaw.policy
    test_policy_check_kill_switch_active()
    test_policy_check_kill_switch_inactive()
    test_policy_assert_shell_allowed()
    test_policy_assert_shell_denied()
    test_policy_assert_shell_empty_cmd()
    test_policy_load_from_file()
    test_policy_load_default_when_file_missing()
    test_policy_assert_fs_read_exact_prefix()
    test_policy_assert_fs_write_allowed_denied()

    # openclaw.tools
    import pathlib
    _tmp = pathlib.Path(tempfile.mkdtemp())
    test_tool_runner_read_allowed(_tmp)
    test_tool_runner_read_denied(_tmp)
    test_tool_runner_write_allowed(_tmp)
    test_tool_runner_write_denied(_tmp)
    test_tool_runner_shell_allowed(_tmp)
    test_tool_runner_shell_denied(_tmp)
    test_tool_runner_budget_exceeded(_tmp)
    test_tool_runner_kill_switch(pathlib.Path(tempfile.mkdtemp()))
    test_tool_runner_call_count_increments(pathlib.Path(tempfile.mkdtemp()))

    # openplanter.dag
    test_dag_add_and_ready()
    test_dag_dependency_blocks_ready()
    test_dag_dependency_unblocked_after_done()
    test_dag_mark_state_transitions()
    test_dag_mark_failed()
    test_dag_mark_nonexistent_job_noop()
    test_dag_spine_written()
    test_dag_no_ready_when_all_done()

    # evezos.manifest edge cases
    test_manifest_missing_file_fails_verify()
    test_manifest_tampered_file_fails_verify()
    test_manifest_missing_manifest_json()
    test_build_manifest_empty_spine()

    print()
    print("ALL EXTENDED TESTS PASSED")
