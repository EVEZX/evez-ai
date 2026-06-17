#!/usr/bin/env python3
"""
EVEZ Meta-Learner — the system learns how to learn better.
Tracks which reasoning strategies work for which problem types,
adjusts strategy selection, identifies new problem categories,
and writes meta-learning state to runtime/meta_learning.json.
Periodically summarizes lessons into DECISIONS/lessons/.
"""
import copy
import os
import sys
import json
import hashlib
import datetime

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
from reasoning.engine import (
    load_recent_traces, load_json, save_json, now_iso, chain_hash, get_genesis_hash,
)

META_STATE_PATH = os.path.join(BASE_DIR, "runtime", "meta_learning.json")
LESSONS_DIR = os.path.join(BASE_DIR, "DECISIONS", "lessons")

DEFAULT_STRATEGIES = {
    "chain": {"success_rate": 0.7, "uses": 0, "successes": 0},
    "tree": {"success_rate": 0.6, "uses": 0, "successes": 0},
    "analogical": {"success_rate": 0.5, "uses": 0, "successes": 0},
    "counterfactual": {"success_rate": 0.5, "uses": 0, "successes": 0},
}


def load_meta_state():
    """Load or initialize meta-learning state."""
    state = load_json(META_STATE_PATH, None)
    if state is None:
        state = {
            "strategies": copy.deepcopy(DEFAULT_STRATEGIES),
            "problem_categories": {},
            "total_reasoning_episodes": 0,
            "lessons_generated": 0,
            "last_updated": now_iso(),
        }
    return state


def save_meta_state(state):
    """Persist meta-learning state."""
    state["last_updated"] = now_iso()
    save_json(META_STATE_PATH, state)


# ---------------------------------------------------------------------------
# Strategy tracking
# ---------------------------------------------------------------------------

def record_outcome(state, reasoning_type, success):
    """Record whether a reasoning strategy succeeded or failed."""
    if reasoning_type not in state["strategies"]:
        state["strategies"][reasoning_type] = {
            "success_rate": 0.5,
            "uses": 0,
            "successes": 0,
        }

    strat = state["strategies"][reasoning_type]
    strat["uses"] += 1
    if success:
        strat["successes"] += 1

    # Update success rate with smoothing
    if strat["uses"] > 0:
        strat["success_rate"] = round(strat["successes"] / strat["uses"], 3)

    state["total_reasoning_episodes"] += 1
    return state


def select_strategy(state, problem_category=None):
    """Select the best reasoning strategy based on historical success rates."""
    strategies = state.get("strategies", DEFAULT_STRATEGIES)

    # If we have a known problem category, use its preferred strategy
    if problem_category and problem_category in state.get("problem_categories", {}):
        cat = state["problem_categories"][problem_category]
        preferred = cat.get("preferred_strategy")
        if preferred and preferred in strategies:
            return preferred

    # Otherwise, pick the strategy with the highest success rate
    best = max(strategies.items(), key=lambda x: x[1]["success_rate"])
    return best[0]


# ---------------------------------------------------------------------------
# Problem categorization
# ---------------------------------------------------------------------------

def categorize_problem(state, problem, category=None):
    """Categorize a problem and track category-strategy mappings."""
    if category is None:
        # Simple keyword-based categorization
        lower = problem.lower()
        if any(w in lower for w in ["uptime", "monitor", "health", "repair"]):
            category = "operational"
        elif any(w in lower for w in ["build", "create", "spawn", "new"]):
            category = "expansion"
        elif any(w in lower for w in ["optimize", "improve", "refactor"]):
            category = "optimization"
        elif any(w in lower for w in ["coordinate", "communicate", "sync"]):
            category = "coordination"
        elif any(w in lower for w in ["revenue", "money", "earn", "monetize"]):
            category = "revenue"
        else:
            category = "general"

    if category not in state["problem_categories"]:
        state["problem_categories"][category] = {
            "count": 0,
            "preferred_strategy": None,
            "strategy_results": {},
        }

    state["problem_categories"][category]["count"] += 1
    return category


def update_category_strategy(state, category, strategy, success):
    """Update which strategy works best for a given problem category."""
    if category not in state["problem_categories"]:
        return

    cat = state["problem_categories"][category]
    if strategy not in cat["strategy_results"]:
        cat["strategy_results"][strategy] = {"uses": 0, "successes": 0}

    cat["strategy_results"][strategy]["uses"] += 1
    if success:
        cat["strategy_results"][strategy]["successes"] += 1

    # Update preferred strategy for this category
    best = None
    best_rate = 0
    for s, data in cat["strategy_results"].items():
        if data["uses"] > 0:
            rate = data["successes"] / data["uses"]
            if rate > best_rate:
                best_rate = rate
                best = s
    cat["preferred_strategy"] = best


# ---------------------------------------------------------------------------
# Lesson generation
# ---------------------------------------------------------------------------

def analyze_traces(traces):
    """Analyze recent reasoning traces to extract patterns."""
    if not traces:
        return None

    type_counts = {}
    confidence_sums = {}
    type_critiques = {}

    for t in traces:
        rtype = t.get("reasoning_type", "unknown")
        type_counts[rtype] = type_counts.get(rtype, 0) + 1

        # Collect confidence data
        steps = t.get("steps", [])
        confs = [s.get("confidence", 0) for s in steps]
        avg = sum(confs) / len(confs) if confs else 0
        confidence_sums[rtype] = confidence_sums.get(rtype, [])
        confidence_sums[rtype].append(avg)

        # Track critique severity
        critique = t.get("self_critique", "")
        type_critiques[rtype] = type_critiques.get(rtype, [])
        type_critiques[rtype].append(critique)

    analysis = {
        "traces_analyzed": len(traces),
        "type_distribution": type_counts,
        "avg_confidence_by_type": {
            k: round(sum(v) / len(v), 3) for k, v in confidence_sums.items() if v
        },
        "critique_counts": {k: len(v) for k, v in type_critiques.items()},
    }
    return analysis


def generate_lesson(state, analysis):
    """Generate a lesson from analysis of reasoning traces."""
    if not analysis:
        return None

    lesson = {
        "type": "meta_learning_lesson",
        "timestamp": now_iso(),
        "episode_count": state["total_reasoning_episodes"],
        "analysis": analysis,
        "insights": [],
    }

    # Insight 1: Most effective strategy
    strategies = state.get("strategies", {})
    if strategies:
        best = max(strategies.items(), key=lambda x: x[1]["success_rate"])
        lesson["insights"].append({
            "insight": f"Most effective strategy: {best[0]} (success rate: {best[1]['success_rate']})",
            "action": f"Prefer {best[0]} for unclassified problems",
        })

    # Insight 2: Underused strategies
    for name, data in strategies.items():
        if data["uses"] < 3:
            lesson["insights"].append({
                "insight": f"Strategy '{name}' is underused ({data['uses']} uses)",
                "action": f"Consider trying {name} for more problem types",
            })

    # Insight 3: Problem category coverage
    categories = state.get("problem_categories", {})
    if categories:
        top_cat = max(categories.items(), key=lambda x: x[1]["count"])
        lesson["insights"].append({
            "insight": f"Most common problem category: {top_cat[0]} ({top_cat[1]['count']} problems)",
            "action": f"Optimize strategies for {top_cat[0]} problems",
        })

    lesson["chain_hash"] = chain_hash(get_genesis_hash(), {
        "timestamp": lesson["timestamp"],
        "episode_count": lesson["episode_count"],
    })

    return lesson


def save_lesson(lesson):
    """Save a lesson to DECISIONS/lessons/."""
    os.makedirs(LESSONS_DIR, exist_ok=True)
    ts = lesson["timestamp"].replace(":", "-").replace(".", "-")
    path = os.path.join(LESSONS_DIR, f"{ts}_lesson.json")
    save_json(path, lesson)
    return path


# ---------------------------------------------------------------------------
# Main meta-learning cycle
# ---------------------------------------------------------------------------

def meta_learn():
    """Run a full meta-learning cycle."""
    state = load_meta_state()

    # Load recent reasoning traces
    traces = load_recent_traces(limit=20)

    # Analyze traces
    analysis = analyze_traces(traces)

    # Categorize and record outcomes from traces
    for t in traces:
        problem = t.get("problem", "")
        rtype = t.get("reasoning_type", "chain")
        critique = t.get("self_critique", "")

        category = categorize_problem(state, problem)
        success = "No flaws" in critique or "sound" in critique
        record_outcome(state, rtype, success)
        update_category_strategy(state, category, rtype, success)

    # Generate lesson if enough data
    if state["total_reasoning_episodes"] > 0 and analysis:
        lesson = generate_lesson(state, analysis)
        if lesson:
            path = save_lesson(lesson)
            state["lessons_generated"] += 1
            return state, lesson, path

    save_meta_state(state)
    return state, None, None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n🎓 EVEZ Meta-Learner — {now_iso()}")

    state, lesson, path = meta_learn()

    print(f"  Total episodes: {state['total_reasoning_episodes']}")
    print(f"  Strategies tracked: {len(state['strategies'])}")
    print(f"  Problem categories: {len(state['problem_categories'])}")

    if lesson:
        print(f"  Lesson generated: {os.path.basename(path)}")
        for insight in lesson.get("insights", []):
            print(f"    → {insight['insight']}")
    else:
        print("  No lesson generated (insufficient data)")

    # Save state
    save_meta_state(state)
    print(f"  State saved to {META_STATE_PATH}")

    # Show strategy recommendations
    best = select_strategy(state)
    print(f"  Recommended default strategy: {best}")

    print("  ✅ Meta-learning cycle complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"meta_learner fatal: {e}")
        sys.exit(0)
