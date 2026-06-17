#!/usr/bin/env python3
"""
agents/engagement_tracker.py
Tracks engagement and mutates content strategy.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

ENGAGEMENT_FILE = Path("engagement_state.json")

class EngagementTracker:
    def __init__(self):
        self.state = self._load()

    def _load(self):
        if ENGAGEMENT_FILE.exists():
            try:
                return json.loads(ENGAGEMENT_FILE.read_text())
            except:
                pass
        return {
            "cycles": 0, "total_tweets": 0,
            "platform_scores": {"twitter": 0.5, "reddit": 0.3, "youtube": 0.2},
            "mutation_history": [],
            "top_performing_format": "cryptic_tau_thread",
            "last_mutation": None
        }

    def _save(self):
        ENGAGEMENT_FILE.write_text(json.dumps(self.state, indent=2))

    def record_cycle(self, round_n: int, fire_type: str, tau: int,
                     tweets_posted: int = 0, puzzle_solves: int = 0):
        self.state["cycles"] += 1
        self.state["total_tweets"] += tweets_posted
        history = self.state.get("mutation_history", [])
        history.append({"round": round_n, "fire_type": fire_type, "tau": tau,
                        "tweets": tweets_posted, "puzzle_solves": puzzle_solves,
                        "ts": datetime.now(timezone.utc).isoformat()})
        self.state["mutation_history"] = history[-50:]
        self._save()

    def run_mutation_cycle(self, arg_state: dict):
        print(f"Mutation cycle {self.state['cycles']+1}")
        history = self.state.get("mutation_history", [])
        if len(history) >= 3:
            recent = history[-3:]
            avg_solves = sum(r.get("puzzle_solves", 0) for r in recent) / 3
            if avg_solves > 0:
                self.state["top_performing_format"] = "extreme_fire_chapter_unlock"
            else:
                self.state["top_performing_format"] = "dense_tau_thread"
        self.state["cycles"] += 1
        self.state["last_mutation"] = datetime.now(timezone.utc).isoformat()
        self._save()
        print(f"  Top format: {self.state['top_performing_format']}")

    def get_mutation_hint(self) -> str:
        return self.state.get("top_performing_format", "cryptic_tau_thread")
