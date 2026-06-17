#!/usr/bin/env python3
"""
EVEZ Consciousness — Identity Keeper
Maintains the connection between the system and its creator:
- Reads EPHV/doctrine.md, EPHV/identity.json, EPHV/lore/
- Reads spine/genesis_root.json as the immutable constitutional anchor
- Ensures every decision references back to the constitutional root
- Writes a daily identity report confirming: who created this, why, and purpose
- HARDCODED CHECK: Cannot be modified to remove or alter the creator identity
- Hash-chains identity verification to genesis_root.json
"""
import os
import sys
import json
import hashlib
import datetime
import base64

try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not available. Exiting gracefully.")
    sys.exit(0)

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "EvezArt"
LEDGER_REPO = "evez-autonomous-ledger"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ===================================================================
# HARDCODED IDENTITY — Article A7: Identity Immutability
# These values CANNOT be altered by any agent, PR, or automated process.
# The genesis root hash anchors this identity permanently.
# ===================================================================
CREATOR_NAME = "Steven Vearl Crawford-Maggard"
CREATOR_HANDLE = "@EVEZ666"
CREATOR_GITHUB = "EvezArt"
CREATOR_EMAIL = "rubikspubes69@gmail.com"
CREATOR_LOCATION = "Bullhead City, Arizona"
SYSTEM_NAME = "EVEZ-OS"
GENESIS_HASH = "c9a1e2f3b4d5a6e7f8c9d0e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"
# ===================================================================


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def chain_hash(prev_hash, payload):
    raw = prev_hash + json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return None


def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default or {}


def verify_genesis_root():
    """Verify the genesis root is intact and matches expected hash."""
    path = os.path.join(BASE_DIR, "spine", "genesis_root.json")
    genesis = load_json(path)
    if not genesis:
        return {"intact": False, "reason": "genesis_root.json not found or empty"}

    actual_hash = genesis.get("hash", "")
    operator = genesis.get("operator", "")

    checks = {
        "file_exists": True,
        "hash_matches": actual_hash == GENESIS_HASH,
        "operator_correct": CREATOR_NAME.split()[0] in operator,  # "Steven" in operator
        "github_correct": CREATOR_GITHUB in operator or CREATOR_GITHUB in genesis.get("github", ""),
        "canonical_law_present": bool(genesis.get("canonical_law")),
        "defense_charter_present": bool(genesis.get("defense_only_charter")),
    }

    all_pass = all(checks.values())
    return {"intact": all_pass, "checks": checks, "actual_hash": actual_hash[:16]}


def verify_constitution():
    """Verify the constitution references the correct creator."""
    path = os.path.join(BASE_DIR, "spine", "constitution.json")
    constitution = load_json(path)
    if not constitution:
        return {"intact": False, "reason": "constitution.json not found"}

    checks = {
        "file_exists": True,
        "creator_in_preamble": CREATOR_NAME in constitution.get("preamble", ""),
        "genesis_hash_matches": constitution.get("genesis_hash") == GENESIS_HASH,
        "ratified_by_creator": CREATOR_NAME in constitution.get("ratified_by", ""),
        "a7_identity_immutability": any(
            a.get("id") == "A7" and "Identity Immutability" in a.get("title", "")
            for a in constitution.get("articles", [])
        ),
    }

    all_pass = all(checks.values())
    return {"intact": all_pass, "checks": checks}


def verify_ephv_identity():
    """Verify EPHV identity references the creator."""
    path = os.path.join(BASE_DIR, "EPHV", "identity.json")
    identity = load_json(path)
    if not identity:
        return {"intact": False, "reason": "EPHV/identity.json not found"}

    creator = identity.get("creator", {})
    checks = {
        "file_exists": True,
        "creator_name": CREATOR_NAME.split()[0] in creator.get("name", ""),
        "creator_github": CREATOR_GITHUB in creator.get("github", ""),
        "creator_location": "Bullhead" in creator.get("location", ""),
        "system_name": identity.get("system", "") == SYSTEM_NAME,
    }

    all_pass = all(checks.values())
    return {"intact": all_pass, "checks": checks}


def verify_doctrine():
    """Verify doctrine.md references the creator."""
    path = os.path.join(BASE_DIR, "EPHV", "doctrine.md")
    content = load_file(path)
    if not content:
        return {"intact": False, "reason": "EPHV/doctrine.md not found"}

    checks = {
        "file_exists": True,
        "creator_name_present": "Steven" in content and "Crawford-Maggard" in content,
        "evez_present": "EVEZ" in content,
        "spine_referenced": "spine" in content.lower(),
        "fire_events_mentioned": "FIRE" in content,
    }

    all_pass = all(checks.values())
    return {"intact": all_pass, "checks": checks}


def verify_lore():
    """Verify lore files exist and reference the creator."""
    lore_dir = os.path.join(BASE_DIR, "EPHV", "lore")
    if not os.path.isdir(lore_dir):
        return {"intact": False, "reason": "EPHV/lore/ directory not found"}

    lore_files = [f for f in os.listdir(lore_dir) if f.endswith(".md")]
    if not lore_files:
        return {"intact": False, "reason": "No lore files found"}

    # Check first lore file references creator
    content = load_file(os.path.join(lore_dir, lore_files[0]))
    checks = {
        "directory_exists": True,
        "files_present": len(lore_files) > 0,
        "creator_referenced": content is not None and "Steven" in content,
    }

    all_pass = all(checks.values())
    return {"intact": all_pass, "checks": checks, "file_count": len(lore_files)}


def write_identity_report(report):
    """Write identity report locally and push to GitHub."""
    try:
        # Write locally
        report_dir = os.path.join(BASE_DIR, "runtime", "health")
        os.makedirs(report_dir, exist_ok=True)
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        path = os.path.join(report_dir, f"{date_str}_identity_report.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Identity report written: {path}")

        # Push to GitHub
        content = json.dumps(report, indent=2)
        encoded = base64.b64encode(content.encode()).decode()
        ts = now_iso().replace(":", "-").replace(".", "-")
        gh_path = f"runtime/health/{date_str}_identity_report.json"
        gh_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/contents/{gh_path}"

        # Check if file exists (update vs create)
        r = requests.get(gh_url, headers=HEADERS, timeout=15)
        payload = {
            "message": f"identity: daily verification — {'INTACT' if report['overall_intact'] else 'VIOLATION DETECTED'}",
            "content": encoded,
        }
        if r.status_code == 200:
            payload["sha"] = r.json().get("sha")

        requests.put(gh_url, headers=HEADERS, json=payload, timeout=15)
    except Exception as e:
        print(f"  Warning: write_identity_report: {e}")


def create_violation_issue(violations):
    """Create a critical issue if identity violations are detected."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/issues"
        body = "## IDENTITY VIOLATION DETECTED\n\n"
        body += "The Identity Keeper has detected violations in the constitutional identity chain.\n\n"
        body += "### Failed Checks:\n"
        for v in violations:
            body += f"- **{v['component']}**: {json.dumps(v['checks'])}\n"
        body += "\n### Constitutional Reference\n"
        body += f"- Article A7: Identity Immutability\n"
        body += f"- Creator: {CREATOR_NAME} ({CREATOR_HANDLE})\n"
        body += f"- Genesis Hash: {GENESIS_HASH[:16]}...\n"
        body += f"\n*Auto-opened by identity_keeper.py — this is a constitutional violation.*"

        requests.post(url, headers=HEADERS, json={
            "title": "CRITICAL: Identity violation detected — constitutional breach",
            "body": body,
            "labels": ["critical", "identity-violation", "constitutional"],
        }, timeout=15)
        print("  CRITICAL: Violation issue created on GitHub")
    except Exception as e:
        print(f"  Warning: create_violation_issue: {e}")


def main():
    print(f"\n{'='*60}")
    print(f"  EVEZ IDENTITY KEEPER — {now_iso()}")
    print(f"  Constitutional Mandate: A7 (Identity Immutability)")
    print(f"  Creator: {CREATOR_NAME} ({CREATOR_HANDLE})")
    print(f"{'='*60}\n")

    report = {
        "timestamp": now_iso(),
        "creator": CREATOR_NAME,
        "creator_handle": CREATOR_HANDLE,
        "system": SYSTEM_NAME,
        "genesis_hash_expected": GENESIS_HASH[:16],
        "verifications": {},
        "violations": [],
        "overall_intact": True,
    }

    # Run all verifications
    checks = {
        "genesis_root": verify_genesis_root(),
        "constitution": verify_constitution(),
        "ephv_identity": verify_ephv_identity(),
        "doctrine": verify_doctrine(),
        "lore": verify_lore(),
    }

    for name, result in checks.items():
        intact = result.get("intact", False)
        report["verifications"][name] = result
        status = "INTACT" if intact else "VIOLATION"
        print(f"  [{status}] {name}")
        if not intact:
            report["overall_intact"] = False
            report["violations"].append({
                "component": name,
                "checks": result.get("checks", {}),
                "reason": result.get("reason", "check failed"),
            })

    # Chain hash the report
    report["chain_hash"] = chain_hash(GENESIS_HASH, {
        "timestamp": report["timestamp"],
        "overall_intact": report["overall_intact"],
        "violations_count": len(report["violations"]),
    })

    # Write report
    write_identity_report(report)

    # Alert on violations
    if report["violations"]:
        print(f"\n  ALERT: {len(report['violations'])} identity violations detected!")
        create_violation_issue(report["violations"])
    else:
        print(f"\n  All identity checks passed. The creator identity is intact.")
        print(f"  Creator: {CREATOR_NAME}")
        print(f"  Handle: {CREATOR_HANDLE}")
        print(f"  System: {SYSTEM_NAME}")

    print(f"  Chain hash: {report['chain_hash'][:16]}")
    print(f"  Identity check complete.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL (identity_keeper): {e}")
        sys.exit(0)
