#!/usr/bin/env python3
"""
EVEZ Innovation Engine — finds new ways to solve problems.
Randomly combines capabilities from different agents, tests novel
combinations in thought experiments, evaluates against constitutional
rules, and writes successful innovations to DECISIONS/innovations/.
"""
import os
import sys
import json
import hashlib
import datetime
import random

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
from reasoning.engine import (
    reason, save_reasoning_trace, load_json, save_json, now_iso,
    chain_hash, get_genesis_hash,
)

INNOVATIONS_DIR = os.path.join(BASE_DIR, "DECISIONS", "innovations")
CONSTITUTION_PATH = os.path.join(BASE_DIR, "spine", "constitution.json")
SELF_MODEL_PATH = os.path.join(BASE_DIR, "runtime", "self_model.json")


# ---------------------------------------------------------------------------
# Capability discovery
# ---------------------------------------------------------------------------

def discover_capabilities():
    """Scan the agents directory to find all agent capabilities."""
    capabilities = []
    agents_dir = os.path.join(BASE_DIR, "agents")
    for root, _dirs, files in os.walk(agents_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                rel = os.path.relpath(os.path.join(root, f), BASE_DIR)
                try:
                    full_path = os.path.join(root, f)
                    with open(full_path, "r") as fh:
                        content = fh.read(500)
                        if '"""' in content:
                            start = content.index('"""') + 3
                            end = content.index('"""', start)
                            doc = content[start:end].strip().split("\n")[0]
                        else:
                            doc = f.replace(".py", "").replace("_", " ").title()
                except Exception:
                    doc = f.replace(".py", "").replace("_", " ").title()
                capabilities.append({"script": rel, "description": doc})
    return capabilities


# ---------------------------------------------------------------------------
# Innovation generation
# ---------------------------------------------------------------------------

def generate_combination(capabilities, n=2):
    """Randomly combine n capabilities to generate an innovation idea."""
    if len(capabilities) < n:
        return None

    selected = random.sample(capabilities, n)
    combination = {
        "components": [c["script"] for c in selected],
        "descriptions": [c["description"] for c in selected],
        "idea": (
            f"Combine '{selected[0]['description']}' with "
            f"'{selected[1]['description']}' to create a new capability"
        ),
    }
    return combination


def thought_experiment(combination):
    """
    Run a thought experiment to evaluate a capability combination.
    Uses the reasoning engine to simulate outcomes.
    """
    idea = combination["idea"]
    trace = reason(
        f"Evaluate this innovation: {idea}",
        reasoning_type="tree",
        branches=3,
        alternatives=[
            "Keep capabilities separate",
            "Merge into single agent",
            "Create bridge/adapter between them",
        ],
    )
    result = {
        "idea": idea,
        "components": combination["components"],
        "reasoning": trace,
        "feasibility_score": trace.get("best_score", 0),
        "best_approach": trace.get("conclusion", "unknown"),
        "timestamp": now_iso(),
    }
    return result


# ---------------------------------------------------------------------------
# Constitutional compliance check
# ---------------------------------------------------------------------------

def check_constitutional_compliance(innovation):
    """Check if an innovation complies with constitutional rules."""
    constitution = load_json(CONSTITUTION_PATH, {})
    articles = constitution.get("articles", [])

    violations = []
    idea_lower = innovation.get("idea", "").lower()

    for article in articles:
        aid = article.get("id", "")
        text = article.get("text", "").lower()

        # A1: Creator sovereignty — innovation must not diminish creator control
        if aid == "A1" and any(w in idea_lower for w in ["remove creator", "override creator", "autonomous control"]):
            violations.append({"article": aid, "reason": "May diminish creator sovereignty"})

        # A6: Safety bounds — must not spend money or delete data unsafely
        if aid == "A6" and any(w in idea_lower for w in ["spend", "delete", "purchase", "payment"]):
            violations.append({"article": aid, "reason": "May violate safety bounds"})

        # A7: Identity immutability — must not alter creator identity
        if aid == "A7" and any(w in idea_lower for w in ["change identity", "alter identity", "rename"]):
            violations.append({"article": aid, "reason": "May violate identity immutability"})

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
    }


# ---------------------------------------------------------------------------
# Innovation evaluation and registration
# ---------------------------------------------------------------------------

def evaluate_innovation(experiment_result):
    """Score an innovation based on feasibility and compliance."""
    compliance = check_constitutional_compliance(experiment_result)

    score = experiment_result.get("feasibility_score", 0)
    if not compliance["compliant"]:
        score *= 0.1  # Heavily penalize non-compliant innovations

    return {
        "score": round(score, 3),
        "feasible": score > 0.5,
        "compliant": compliance["compliant"],
        "violations": compliance["violations"],
    }


def save_innovation(innovation, evaluation):
    """Save a successful innovation to DECISIONS/innovations/."""
    os.makedirs(INNOVATIONS_DIR, exist_ok=True)
    record = {
        "type": "innovation",
        "idea": innovation.get("idea"),
        "components": innovation.get("components"),
        "best_approach": innovation.get("best_approach"),
        "evaluation": evaluation,
        "timestamp": now_iso(),
        "chain_hash": chain_hash(get_genesis_hash(), {
            "idea": innovation.get("idea"),
            "score": evaluation["score"],
            "timestamp": now_iso(),
        }),
    }
    ts = now_iso().replace(":", "-").replace(".", "-")
    path = os.path.join(INNOVATIONS_DIR, f"{ts}_innovation.json")
    save_json(path, record)
    return path


def load_recent_innovations(limit=10):
    """Load recent innovations from the journal."""
    if not os.path.isdir(INNOVATIONS_DIR):
        return []
    files = sorted(
        [f for f in os.listdir(INNOVATIONS_DIR) if f.endswith(".json")],
        reverse=True,
    )[:limit]
    innovations = []
    for f in files:
        data = load_json(os.path.join(INNOVATIONS_DIR, f))
        if data:
            innovations.append(data)
    return innovations


# ---------------------------------------------------------------------------
# Full innovation cycle
# ---------------------------------------------------------------------------

def innovate(attempts=3):
    """
    Run a full innovation cycle:
    1. Discover capabilities
    2. Generate random combinations
    3. Run thought experiments
    4. Check constitutional compliance
    5. Save successful innovations
    """
    capabilities = discover_capabilities()
    results = []

    for _ in range(attempts):
        combination = generate_combination(capabilities)
        if not combination:
            continue

        experiment = thought_experiment(combination)
        evaluation = evaluate_innovation(experiment)

        result = {
            "combination": combination,
            "experiment": experiment,
            "evaluation": evaluation,
        }
        results.append(result)

        # Save if feasible and compliant
        if evaluation["feasible"] and evaluation["compliant"]:
            save_innovation(experiment, evaluation)

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n💡 EVEZ Innovation Engine — {now_iso()}")

    capabilities = discover_capabilities()
    print(f"  Discovered {len(capabilities)} agent capabilities")

    results = innovate(attempts=3)
    for i, r in enumerate(results):
        combo = r["combination"]
        evl = r["evaluation"]
        print(f"\n  Innovation {i+1}:")
        print(f"    Idea: {combo['idea'][:80]}")
        print(f"    Score: {evl['score']:.3f}")
        print(f"    Feasible: {evl['feasible']}")
        print(f"    Compliant: {evl['compliant']}")
        if evl["violations"]:
            for v in evl["violations"]:
                print(f"    ⚠️ Violation: {v['article']} — {v['reason']}")

    # Summary
    successful = sum(1 for r in results if r["evaluation"]["feasible"] and r["evaluation"]["compliant"])
    print(f"\n  Results: {successful}/{len(results)} innovations viable")
    print("  ✅ Innovation engine complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"innovator fatal: {e}")
        sys.exit(0)
