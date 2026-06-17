#!/usr/bin/env python3
"""
EVEZ Agent Communication Protocol — structured inter-agent messaging.
Message types: QUERY, RESPONSE, PROPOSAL, VOTE, CONSENSUS, DELEGATION, ESCALATION.
Conflict resolution escalates to the reasoning engine.
Communication log at runtime/comms_log.jsonl.
"""
import os
import sys
import json
import hashlib
import datetime

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMMS_LOG_PATH = os.path.join(BASE_DIR, "runtime", "comms_log.jsonl")

MESSAGE_TYPES = [
    "QUERY",
    "RESPONSE",
    "PROPOSAL",
    "VOTE",
    "CONSENSUS",
    "DELEGATION",
    "ESCALATION",
]

PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def message_hash(message):
    raw = json.dumps(message, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Message construction
# ---------------------------------------------------------------------------

def create_message(sender_agent, recipient_agent, intent, content,
                   priority="MEDIUM", msg_type="QUERY", reference_id=None):
    """Create a structured inter-agent message."""
    if msg_type not in MESSAGE_TYPES:
        msg_type = "QUERY"
    if priority not in PRIORITIES:
        priority = "MEDIUM"

    msg = {
        "sender_agent": sender_agent,
        "recipient_agent": recipient_agent,
        "msg_type": msg_type,
        "intent": intent,
        "content": content,
        "priority": priority,
        "timestamp": now_iso(),
        "reference_id": reference_id,
    }
    msg["message_id"] = message_hash(msg)
    return msg


def create_query(sender, recipient, question, priority="MEDIUM"):
    """Agent asks another agent a question."""
    return create_message(sender, recipient, "ask", question,
                          priority=priority, msg_type="QUERY")


def create_response(sender, recipient, answer, reference_id, priority="MEDIUM"):
    """Agent responds to a query."""
    return create_message(sender, recipient, "answer", answer,
                          priority=priority, msg_type="RESPONSE",
                          reference_id=reference_id)


def create_proposal(sender, proposal_text, priority="MEDIUM"):
    """Agent proposes an action to all agents (broadcast)."""
    return create_message(sender, "ALL", "propose", proposal_text,
                          priority=priority, msg_type="PROPOSAL")


def create_vote(sender, proposal_id, vote_value, reason=""):
    """Agent votes on a proposal. vote_value: 'approve', 'reject', 'abstain'."""
    content = {"vote": vote_value, "reason": reason}
    return create_message(sender, "ALL", "vote", content,
                          priority="MEDIUM", msg_type="VOTE",
                          reference_id=proposal_id)


def create_consensus(topic, outcome, votes):
    """Record a consensus decision."""
    content = {
        "topic": topic,
        "outcome": outcome,
        "votes_for": sum(1 for v in votes if v.get("content", {}).get("vote") == "approve"),
        "votes_against": sum(1 for v in votes if v.get("content", {}).get("vote") == "reject"),
        "votes_abstain": sum(1 for v in votes if v.get("content", {}).get("vote") == "abstain"),
    }
    return create_message("system", "ALL", "consensus_reached", content,
                          priority="HIGH", msg_type="CONSENSUS")


def create_delegation(sender, recipient, task, priority="MEDIUM"):
    """Delegate a task to another agent."""
    return create_message(sender, recipient, "delegate", task,
                          priority=priority, msg_type="DELEGATION")


def create_escalation(sender, issue, priority="HIGH"):
    """Escalate an issue to the reasoning engine for conflict resolution."""
    return create_message(sender, "reasoning_engine", "escalate", issue,
                          priority=priority, msg_type="ESCALATION")


# ---------------------------------------------------------------------------
# Communication log
# ---------------------------------------------------------------------------

def log_message(message):
    """Append a message to the communication log."""
    os.makedirs(os.path.dirname(COMMS_LOG_PATH), exist_ok=True)
    with open(COMMS_LOG_PATH, "a") as f:
        f.write(json.dumps(message) + "\n")
    return message["message_id"]


def read_log(limit=50):
    """Read the most recent messages from the communication log."""
    if not os.path.isfile(COMMS_LOG_PATH):
        return []
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
        return []
    return messages[-limit:]


def get_messages_for_agent(agent_name, limit=20):
    """Get messages addressed to a specific agent."""
    all_msgs = read_log(limit=200)
    return [
        m for m in all_msgs
        if m.get("recipient_agent") in (agent_name, "ALL")
    ][-limit:]


def get_proposals(limit=10):
    """Get recent proposals."""
    all_msgs = read_log(limit=200)
    return [m for m in all_msgs if m.get("msg_type") == "PROPOSAL"][-limit:]


def get_votes_for_proposal(proposal_id):
    """Get all votes for a specific proposal."""
    all_msgs = read_log(limit=500)
    return [
        m for m in all_msgs
        if m.get("msg_type") == "VOTE" and m.get("reference_id") == proposal_id
    ]


def resolve_proposal(proposal_id, threshold=0.5):
    """
    Tally votes for a proposal and return the outcome.
    Returns a consensus message if quorum reached.
    """
    votes = get_votes_for_proposal(proposal_id)
    if not votes:
        return None

    approvals = sum(1 for v in votes if v.get("content", {}).get("vote") == "approve")
    rejections = sum(1 for v in votes if v.get("content", {}).get("vote") == "reject")
    total = approvals + rejections

    if total == 0:
        return None

    approval_rate = approvals / total
    outcome = "approved" if approval_rate >= threshold else "rejected"

    # Find original proposal
    all_msgs = read_log(limit=500)
    proposal = next(
        (m for m in all_msgs if m.get("message_id") == proposal_id),
        None,
    )
    topic = proposal.get("content", "unknown") if proposal else "unknown"

    consensus = create_consensus(topic, outcome, votes)
    log_message(consensus)
    return consensus


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------

def detect_conflicts(messages):
    """Detect conflicting messages (opposing proposals or disagreements)."""
    conflicts = []
    proposals = [m for m in messages if m.get("msg_type") == "PROPOSAL"]
    for i, p1 in enumerate(proposals):
        for p2 in proposals[i + 1:]:
            # Simple heuristic: same intent from different agents
            if (p1.get("sender_agent") != p2.get("sender_agent") and
                    p1.get("intent") == p2.get("intent")):
                conflicts.append({
                    "type": "competing_proposals",
                    "agents": [p1["sender_agent"], p2["sender_agent"]],
                    "proposals": [p1["message_id"], p2["message_id"]],
                })
    return conflicts


def escalate_conflict(conflict):
    """Escalate a detected conflict to the reasoning engine."""
    msg = create_escalation(
        "protocol",
        {
            "conflict_type": conflict["type"],
            "agents_involved": conflict["agents"],
            "details": conflict,
        },
        priority="HIGH",
    )
    log_message(msg)
    return msg


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n📡 EVEZ Communication Protocol — {now_iso()}")

    # Demo: simulate a communication exchange
    q = create_query("synthesizer", "hypothesis_engine", "What hypotheses are pending?")
    log_message(q)
    print(f"  QUERY: {q['sender_agent']} → {q['recipient_agent']}: {q['intent']}")

    r = create_response("hypothesis_engine", "synthesizer", "3 hypotheses pending",
                        reference_id=q["message_id"])
    log_message(r)
    print(f"  RESPONSE: {r['sender_agent']} → {r['recipient_agent']}")

    p = create_proposal("evolve", "Spawn a new reasoning agent for meta-cognition")
    log_message(p)
    print(f"  PROPOSAL: {p['sender_agent']}: {p['content'][:60]}")

    v1 = create_vote("synthesizer", p["message_id"], "approve", "Needed for deeper reasoning")
    v2 = create_vote("watchdog", p["message_id"], "approve", "Aligns with expansion imperative")
    log_message(v1)
    log_message(v2)
    print(f"  VOTES: 2 approve")

    consensus = resolve_proposal(p["message_id"])
    if consensus:
        print(f"  CONSENSUS: {consensus['content']['outcome']}")

    print(f"  Log entries: {len(read_log())}")
    print("  ✅ Communication protocol complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"protocol fatal: {e}")
        sys.exit(0)
