"""
Game Agent Infra CLI — init, cycle, diagram commands.
"""

import argparse
from pathlib import Path
from game_agent_infra.core.spine import AppendOnlySpine
from game_agent_infra.core.cognition_wheel import CognitionWheel, Ring
from game_agent_infra.core.fsc import FSC


def main():
    parser = argparse.ArgumentParser(prog="game-agent-infra")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init")
    p_init.add_argument("--seed", type=int, default=42)

    p_cycle = sub.add_parser("cycle")
    p_cycle.add_argument("--ring", default="R4")
    p_cycle.add_argument("--anomaly", default="DNS resolution timeout")

    args = parser.parse_args()

    data_dir = Path("evez_data")
    spine = AppendOnlySpine(data_dir / "main_spine.jsonl")
    wheel = CognitionWheel()
    fsc = FSC()

    if args.cmd == "init":
        wheel.register("EVEZClaw#1", Ring[args.ring])
        print("Initialized spine + cognition wheel.")
    elif args.cmd == "cycle":
        event = spine.append({"anomaly": args.anomaly, "ring": args.ring})
        cycle = fsc.cycle(args.anomaly, [args.ring])
        print(f"Cycle {cycle.cycle_id} complete. Ω={cycle.Ω}")
        print(f"Spine hash: {event.hash}")


if __name__ == "__main__":
    main()