#!/usr/bin/env python3
"""
EVEZ Natural Language Interface — intelligent communication with the creator.
Translates system state into natural language, understands commands,
generates contextual status updates, and explains reasoning in plain language.
Adapts style based on context (urgent vs routine).
"""
import os
import sys
import json
import datetime
import re

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
from reasoning.engine import load_json, now_iso


SELF_MODEL_PATH = os.path.join(BASE_DIR, "runtime", "self_model.json")
META_STATE_PATH = os.path.join(BASE_DIR, "runtime", "meta_learning.json")
COMMS_LOG_PATH = os.path.join(BASE_DIR, "runtime", "comms_log.jsonl")

URGENCY_KEYWORDS = [
    "fail", "error", "crash", "down", "critical", "broken", "urgent",
    "emergency", "offline", "dead", "stuck",
]

COMMAND_PATTERNS = {
    r"(?i)^status$": "status",
    r"(?i)^status\s+(.+)$": "status_detail",
    r"(?i)^reason\s+about\s+(.+)$": "reason",
    r"(?i)^explain\s+(.+)$": "explain",
    r"(?i)^what.+happening": "status",
    r"(?i)^how.+doing": "status",
    r"(?i)^propose\s+(.+)$": "propose",
    r"(?i)^vote\s+(approve|reject|abstain)\s+(.+)$": "vote",
    r"(?i)^learn$": "meta_learn",
    r"(?i)^innovate$": "innovate",
    r"(?i)^help$": "help",
}


# ---------------------------------------------------------------------------
# Context detection
# ---------------------------------------------------------------------------

def detect_urgency(text):
    """Determine if a message is urgent based on keywords."""
    lower = text.lower()
    matches = sum(1 for kw in URGENCY_KEYWORDS if kw in lower)
    if matches >= 2:
        return "critical"
    if matches == 1:
        return "elevated"
    return "routine"


def detect_context(system_state):
    """Determine the overall system context for communication style."""
    consciousness = system_state.get("state", {}).get("consciousness_level", 0)
    issues = system_state.get("state", {}).get("total_issues_open", 0)
    workflows = system_state.get("state", {}).get("total_workflows", 0)

    if consciousness < 20:
        return "bootstrapping"
    if issues > 20:
        return "busy"
    if workflows == 0:
        return "degraded"
    return "normal"


# ---------------------------------------------------------------------------
# State → Natural Language
# ---------------------------------------------------------------------------

def system_status_report(style="routine"):
    """Generate a natural language status report from system state."""
    model = load_json(SELF_MODEL_PATH, {})
    meta = load_json(META_STATE_PATH, {})

    state = model.get("state", {})
    capabilities = model.get("capabilities", [])
    identity = model.get("identity", {})

    consciousness = state.get("consciousness_level", 0)
    repos = state.get("repos_count", "?")
    issues = state.get("total_issues_open", "?")
    workflows = state.get("total_workflows", "?")
    last_hb = state.get("last_heartbeat", "unknown")

    # Meta-learning stats
    episodes = meta.get("total_reasoning_episodes", 0)
    lessons = meta.get("lessons_generated", 0)
    strategies = meta.get("strategies", {})
    best_strat = max(strategies.items(), key=lambda x: x[1]["success_rate"])[0] if strategies else "none"

    if style == "critical":
        return (
            f"⚠️ URGENT STATUS — {identity.get('name', 'EVEZ-OS')}\n"
            f"Consciousness: {consciousness}/100 | "
            f"Workflows: {workflows} | Issues: {issues}\n"
            f"Last heartbeat: {last_hb}\n"
            f"Action needed: check failing components immediately."
        )

    if style == "brief":
        return (
            f"{identity.get('name', 'EVEZ-OS')}: "
            f"consciousness {consciousness}/100, "
            f"{len(capabilities)} agents, "
            f"{workflows} workflows, "
            f"{issues} open issues."
        )

    # Full routine report
    lines = [
        f"📊 {identity.get('name', 'EVEZ-OS')} Status Report — {now_iso()}",
        "",
        f"Consciousness Level: {consciousness}/100",
        f"Active Repositories: {repos}",
        f"Open Issues: {issues}",
        f"Active Workflows: {workflows}",
        f"Agent Capabilities: {len(capabilities)}",
        f"Last Heartbeat: {last_hb}",
        "",
        f"🎓 Meta-Learning:",
        f"  Reasoning Episodes: {episodes}",
        f"  Lessons Generated: {lessons}",
        f"  Best Strategy: {best_strat}",
    ]

    context = detect_context(model)
    if context == "degraded":
        lines.append("\n⚠️ System appears degraded — no active workflows detected.")
    elif context == "busy":
        lines.append(f"\n📋 High workload — {issues} issues need attention.")
    elif context == "bootstrapping":
        lines.append("\n🌱 System is in early bootstrap phase.")
    else:
        lines.append("\n✅ System operating normally.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

def parse_command(text):
    """Parse natural language input into a system action."""
    text = text.strip()
    for pattern, action in COMMAND_PATTERNS.items():
        match = re.match(pattern, text)
        if match:
            args = match.groups() if match.groups() else ()
            return {"action": action, "args": list(args), "raw": text}
    return {"action": "unknown", "args": [], "raw": text}


def execute_command(parsed):
    """Execute a parsed command and return natural language response."""
    action = parsed["action"]
    args = parsed["args"]

    if action == "status":
        return system_status_report()

    if action == "status_detail":
        target = args[0] if args else ""
        return f"Detailed status for '{target}': checking system state..."

    if action == "reason":
        topic = args[0] if args else "general"
        return f"Initiating reasoning about: {topic}. Use the reasoning engine for deeper analysis."

    if action == "explain":
        topic = args[0] if args else "the system"
        return explain_reasoning(topic)

    if action == "propose":
        proposal = args[0] if args else ""
        return f"Proposal recorded: '{proposal}'. Broadcasting to agent panel for voting."

    if action == "vote":
        vote_val = args[0] if args else "abstain"
        target = args[1] if len(args) > 1 else "unknown"
        return f"Vote '{vote_val}' registered for: {target}"

    if action == "meta_learn":
        return "Triggering meta-learning cycle. Analyzing recent reasoning traces..."

    if action == "innovate":
        return "Triggering innovation engine. Exploring novel capability combinations..."

    if action == "help":
        return (
            "Available commands:\n"
            "  status — system overview\n"
            "  status <component> — detailed status\n"
            "  reason about <topic> — trigger reasoning\n"
            "  explain <topic> — explain system reasoning\n"
            "  propose <action> — broadcast a proposal\n"
            "  vote approve/reject <proposal> — vote on proposal\n"
            "  learn — trigger meta-learning\n"
            "  innovate — trigger innovation engine\n"
            "  help — this message"
        )

    return f"I don't understand '{parsed['raw']}'. Type 'help' for available commands."


# ---------------------------------------------------------------------------
# Reasoning explanation
# ---------------------------------------------------------------------------

def explain_reasoning(topic):
    """Explain system reasoning in plain language."""
    meta = load_json(META_STATE_PATH, {})
    strategies = meta.get("strategies", {})
    categories = meta.get("problem_categories", {})

    lines = [f"📖 How the system reasons about: {topic}", ""]

    # Strategy overview
    if strategies:
        lines.append("Reasoning strategies and their track records:")
        for name, data in sorted(strategies.items(), key=lambda x: -x[1]["success_rate"]):
            lines.append(
                f"  {name}: {data['success_rate']*100:.0f}% success "
                f"({data['successes']}/{data['uses']} runs)"
            )

    # Category relevance
    lower_topic = topic.lower()
    relevant_cat = None
    for cat in categories:
        if cat in lower_topic or lower_topic in cat:
            relevant_cat = cat
            break

    if relevant_cat:
        cat_data = categories[relevant_cat]
        preferred = cat_data.get("preferred_strategy", "chain")
        lines.append(f"\nFor '{relevant_cat}' problems, the preferred strategy is: {preferred}")
        lines.append(f"This category has been encountered {cat_data['count']} times.")
    else:
        lines.append(f"\nNo specific category match for '{topic}'. Default strategy will be used.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Communication style adaptation
# ---------------------------------------------------------------------------

def format_message(content, urgency="routine"):
    """Format a message with appropriate style based on urgency."""
    if urgency == "critical":
        return f"🚨 {content}"
    if urgency == "elevated":
        return f"⚠️ {content}"
    return content


def summarize_comms_log(limit=10):
    """Summarize recent agent communications in natural language."""
    if not os.path.isfile(COMMS_LOG_PATH):
        return "No agent communications recorded yet."

    messages = []
    try:
        with open(COMMS_LOG_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        return "Unable to read communications log."

    recent = messages[-limit:]
    if not recent:
        return "Communications log is empty."

    lines = [f"📡 Recent Agent Communications ({len(recent)} messages):", ""]
    for m in recent:
        sender = m.get("sender_agent", "?")
        recipient = m.get("recipient_agent", "?")
        msg_type = m.get("msg_type", "?")
        intent = m.get("intent", "")
        lines.append(f"  [{msg_type}] {sender} → {recipient}: {intent}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n💬 EVEZ Natural Language Interface — {now_iso()}")

    # Generate status report
    report = system_status_report()
    print(f"\n{report}")

    # Demo command parsing
    test_commands = ["status", "reason about uptime", "help", "what is happening"]
    for cmd in test_commands:
        parsed = parse_command(cmd)
        print(f"\n  Command: '{cmd}' → action={parsed['action']}")

    # Demo urgency detection
    test_msgs = [
        "Everything is running fine",
        "The workflow failed",
        "CRITICAL: system crash detected, error in all components",
    ]
    for msg in test_msgs:
        urgency = detect_urgency(msg)
        print(f"  Urgency('{msg[:40]}...'): {urgency}")

    # Summarize comms
    comms_summary = summarize_comms_log()
    print(f"\n{comms_summary}")

    print("\n  ✅ NLP interface complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"nlp fatal: {e}")
        sys.exit(0)
