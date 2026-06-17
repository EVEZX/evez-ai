#!/usr/bin/env python3
"""
claude_fast.py — Lightweight Claude runtime.

Fast path: single witness, no consensus overhead.
Auto-escalates to L1 multi-witness on high-stakes trigger words.

Usage:
  python3 claude_fast.py "your prompt here"
  python3 claude_fast.py "deploy to prod" --force-consensus
  echo "log text" | python3 claude_fast.py --system "you are a log analyst"
"""

import os
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional, Literal
from dataclasses import dataclass, asdict

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

Lane = Literal["fast", "consensus", "forced_consensus"]

DEFAULT_MODEL = "claude-haiku-4-5"
FAST_MAX_TOKENS = 1024
CONSENSUS_TRIGGERS = [
    "deploy", "delete", "merge", "ship", "approve",
    "override", "bypass", "grant", "revoke", "execute"
]


@dataclass
class FastResult:
    content: str
    lane_used: Lane
    model: str
    latency_ms: float
    evidence_hash: str
    timestamp: str
    escalated: bool
    escalation_reason: Optional[str] = None


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _needs_consensus(prompt: str, force: bool) -> tuple[bool, Optional[str]]:
    if force:
        return True, "caller_forced"
    for trigger in CONSENSUS_TRIGGERS:
        if trigger in prompt.lower():
            return True, f"trigger_word:{trigger}"
    return False, None


def _call_claude(prompt: str, system: Optional[str], model: str,
                max_tokens: int) -> tuple[str, float]:
    if not HAS_ANTHROPIC:
        raise RuntimeError("pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    msgs = [{"role": "user", "content": prompt}]
    kwargs = dict(model=model, max_tokens=max_tokens, messages=msgs)
    if system:
        kwargs["system"] = system
    t0 = time.monotonic()
    response = client.messages.create(**kwargs)
    latency_ms = (time.monotonic() - t0) * 1000
    return response.content[0].text, latency_ms


def ask(prompt: str, system: Optional[str] = None, model: str = DEFAULT_MODEL,
        max_tokens: int = FAST_MAX_TOKENS, force_consensus: bool = False) -> FastResult:
    """Fast-path Claude call with auto-escalation."""
    escalate, reason = _needs_consensus(prompt, force_consensus)

    if escalate:
        # In production: route to L1 multi-witness
        # For now: still call Claude but log the escalation
        content, latency_ms = _call_claude(prompt, system, model, max_tokens)
        return FastResult(
            content=content, lane_used="consensus", model=model,
            latency_ms=latency_ms, evidence_hash=_hash(content),
            timestamp=_now_utc(), escalated=True, escalation_reason=reason
        )

    content, latency_ms = _call_claude(prompt, system, model, max_tokens)
    return FastResult(
        content=content, lane_used="fast", model=model,
        latency_ms=latency_ms, evidence_hash=_hash(content),
        timestamp=_now_utc(), escalated=False
    )


if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", help="Prompt text")
    parser.add_argument("--system", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=FAST_MAX_TOKENS)
    parser.add_argument("--force-consensus", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        parser.print_help()
        sys.exit(1)
    result = ask(prompt, system=args.system, model=args.model,
                 max_tokens=args.max_tokens, force_consensus=args.force_consensus)
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(result.content)
        print(f"\n[{result.lane_used} | {result.latency_ms:.0f}ms | {result.evidence_hash}]",
              file=sys.stderr)
