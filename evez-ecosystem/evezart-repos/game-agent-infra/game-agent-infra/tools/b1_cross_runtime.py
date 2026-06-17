#!/usr/bin/env python3
"""
b1_cross_runtime.py - Full cross-runtime B1 verification orchestrator

Orchestrates Python + Node.js + Go hash emitters to prove canonical
reproducibility across all three runtimes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Import Python canonical hash function
try:
    from ledger_and_b1_tools import hash_typed_input
except ImportError:
    import hashlib
    import unicodedata

    def normalize_strings(obj):
        if isinstance(obj, str):
            return unicodedata.normalize("NFC", obj)
        if isinstance(obj, list):
            return [normalize_strings(x) for x in obj]
        if isinstance(obj, dict):
            return {k: normalize_strings(v) for k, v in obj.items()}
        return obj

    def canonical_json(obj):
        return json.dumps(
            normalize_strings(obj),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def hash_typed_input(path):
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        return "sha256:" + hashlib.sha256(canonical_json(obj)).hexdigest()


# ─── Runtime emitters ──────────────────────────────────────────────────────────


def run_node_emitter(input_paths, emitter="hash_emitter.js"):
    try:
        result = subprocess.run(
            ["node", emitter, *input_paths],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {p: None for p in input_paths}
        data = json.loads(result.stdout)
        return {p: data[p].get("hash") for p in input_paths if p in data}
    except Exception:
        return {p: None for p in input_paths}


def run_go_emitter(input_paths, emitter="hash_emitter.go"):
    try:
        result = subprocess.run(
            ["go", "run", emitter, *input_paths],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return {p: None for p in input_paths}
        data = json.loads(result.stdout)
        return {p: data[p].get("hash") for p in input_paths if p in data}
    except Exception:
        return {p: None for p in input_paths}


# ─── B1 orchestration ──────────────────────────────────────────────────────────


def run_b1_cycle(input_paths, emitter_dir="."):
    print("[B1] Running Python emitter...", file=sys.stderr)
    python_results = {p: hash_typed_input(p) for p in input_paths}

    print("[B1] Running Node.js emitter...", file=sys.stderr)
    node_results = run_node_emitter(input_paths, f"{emitter_dir}/hash_emitter.js")

    print("[B1] Running Go emitter...", file=sys.stderr)
    go_results = run_go_emitter(input_paths, f"{emitter_dir}/hash_emitter.go")

    cases = []
    all_pass = True

    for path in input_paths:
        py_hash = python_results.get(path)
        node_hash = node_results.get(path)
        go_hash = go_results.get(path)

        known = [h for h in [py_hash, node_hash, go_hash] if h is not None]
        all_equal = len(set(known)) == 1 if known else False
        full_witness = all(h is not None for h in [py_hash, node_hash, go_hash])
        case_passed = all_equal and full_witness

        if not case_passed:
            all_pass = False

        cases.append({
            "input": path,
            "hashes": {"python": py_hash, "node": node_hash, "go": go_hash},
            "all_equal": all_equal,
            "full_witness": full_witness,
            "passed": case_passed,
        })

    return {
        "proof_cycle_id": "B1-0001",
        "proof_type": "canonical_reproducibility",
        "status": "PASS" if all_pass else "FAIL",
        "cases": cases,
        "summary": {
            "total_cases": len(cases),
            "passed_cases": sum(1 for c in cases if c["passed"]),
            "all_fully_witnessed": all(c["full_witness"] for c in cases),
        },
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="B1 cross-runtime verification")
    parser.add_argument("inputs", nargs="+", help="JSON files to verify")
    parser.add_argument("--out", default="b1_cycle_0001_full.json")
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--emitter-dir", default=".")
    args = parser.parse_args()

    print(f"[B1] Running B1 Cycle 1 on {len(args.inputs)} input files", file=sys.stderr)

    if args.python_only:
        cases = []
        for path in args.inputs:
            try:
                py_hash = hash_typed_input(path)
                cases.append({
                    "input": path,
                    "hashes": {"python": py_hash, "node": None, "go": None},
                    "all_equal": True,
                    "full_witness": False,
                    "passed": True,
                })
            except Exception as e:
                cases.append({
                    "input": path,
                    "hashes": {"python": None, "node": None, "go": None},
                    "all_equal": False,
                    "full_witness": False,
                    "passed": False,
                    "error": str(e),
                })

        result = {
            "proof_cycle_id": "B1-0001",
            "proof_type": "canonical_reproducibility",
            "status": "PASS" if all(c["passed"] for c in cases) else "FAIL",
            "cases": cases,
            "summary": {
                "total_cases": len(cases),
                "passed_cases": sum(1 for c in cases if c["passed"]),
                "all_fully_witnessed": False,
            },
        }
    else:
        result = run_b1_cycle(args.inputs, args.emitter_dir)

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[B1] Result: {result['status']}", file=sys.stderr)
    print(json.dumps(result["summary"], indent=2))

    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()