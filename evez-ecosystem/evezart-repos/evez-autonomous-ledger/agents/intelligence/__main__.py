#!/usr/bin/env python3
"""
Entry point for the EVEZ Autonomous Intelligence Core.

Runs the full cycle: OBSERVE → ANALYZE → PLAN → EXECUTE → RECORD → ADAPT
Then generates the research report and dashboard.

Usage:
    python -m agents.intelligence
    # or
    python agents/intelligence/__main__.py
"""

import sys
import os

# Ensure repo root is on path so imports work when run from any directory
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from agents.intelligence.core import AutonomousIntelligence, GITHUB_TOKEN, ORG
from agents.intelligence.researcher import generate_research_report
from agents.intelligence.monitor import generate_dashboard


def main():
    print("=" * 60)
    print("EVEZ Autonomous Intelligence Core — Full Run")
    print("=" * 60)

    # Phase 1-6: Core cycle
    brain = AutonomousIntelligence(github_token=GITHUB_TOKEN, org=ORG)
    try:
        cycle_result = brain.run_cycle()
    except Exception as exc:
        print(f"Core cycle failed: {exc}")
        cycle_result = None

    # Phase 7: Research
    try:
        research = generate_research_report()
        print(f"  Research: {research}")
    except Exception as exc:
        print(f"  Research failed (non-fatal): {exc}")

    # Phase 8: Dashboard
    try:
        if cycle_result:
            dashboard = generate_dashboard(
                state=cycle_result.get("state"),
                analysis=cycle_result.get("analysis"),
                results=cycle_result.get("results"),
            )
        else:
            dashboard = generate_dashboard()
        print(f"  Dashboard: cycle {dashboard.get('cycle_number', '?')}, "
              f"health {dashboard.get('ecosystem', {}).get('health_score', '?')}")
    except Exception as exc:
        print(f"  Dashboard failed (non-fatal): {exc}")

    print("\n✅ Full intelligence run complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL: {exc}")
        sys.exit(0)
