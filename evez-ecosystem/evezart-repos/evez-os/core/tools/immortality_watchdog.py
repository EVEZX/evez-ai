#!/usr/bin/env python3
"""EvezOS immortality watchdog.

Supervises critical EvezBrain services and restarts crashed services with
exponential backoff so no single process failure can permanently kill the stack.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


DEFAULT_SERVICES = {
    "consciousness-api": {
        "command": "python -m uvicorn app:app --host 0.0.0.0 --port 7000",
        "cwd": "services/agent",
    },
    "mesh-network": {
        "command": "npm run dev",
        "cwd": "services/game-server",
    },
    "memory-graph": {
        "command": "npm run dev",
        "cwd": "services/apigw",
    },
    "reward-loop": {
        "command": "python narrative_coherence.py",
        "cwd": ".",
    },
    "emotion-core": {
        "command": "python fire_rekindle_watch.py",
        "cwd": ".",
    },
}


@dataclass
class ServiceState:
    name: str
    command: str
    cwd: Path
    env: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen] = None
    restart_count: int = 0
    backoff_seconds: float = 1.0
    next_restart_after: float = 0.0


class ImmortalityWatchdog:
    def __init__(
        self,
        repo_root: Path,
        services: Dict[str, dict],
        base_backoff: float,
        max_backoff: float,
        poll_interval: float,
    ) -> None:
        self.repo_root = repo_root
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.poll_interval = poll_interval
        self.running = True
        self.services = {
            name: ServiceState(
                name=name,
                command=cfg["command"],
                cwd=(repo_root / cfg.get("cwd", ".")).resolve(),
                env=cfg.get("env", {}),
                backoff_seconds=base_backoff,
            )
            for name, cfg in services.items()
        }

    def _start_service(self, service: ServiceState) -> None:
        merged_env = os.environ.copy()
        merged_env.update(service.env)
        service.process = subprocess.Popen(  # noqa: S603
            shlex.split(service.command),
            cwd=service.cwd,
            env=merged_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[watchdog] started {service.name} (pid={service.process.pid})")

    def _stop_service(self, service: ServiceState) -> None:
        if not service.process:
            return
        if service.process.poll() is None:
            service.process.terminate()
            try:
                service.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                service.process.kill()
                service.process.wait(timeout=5)
        print(f"[watchdog] stopped {service.name}")
        service.process = None

    def _schedule_restart(self, service: ServiceState) -> None:
        service.restart_count += 1
        wait_for = min(service.backoff_seconds, self.max_backoff)
        service.next_restart_after = time.time() + wait_for
        service.backoff_seconds = min(wait_for * 2, self.max_backoff)
        print(
            f"[watchdog] {service.name} crashed; restarting in {wait_for:.1f}s "
            f"(restart #{service.restart_count})"
        )

    def boot(self) -> None:
        for service in self.services.values():
            self._start_service(service)

    def loop(self) -> None:
        self.boot()
        while self.running:
            now = time.time()
            for service in self.services.values():
                if service.process and service.process.poll() is not None:
                    self._schedule_restart(service)
                    service.process = None
                if service.process is None and now >= service.next_restart_after:
                    self._start_service(service)
            time.sleep(self.poll_interval)

    def shutdown(self) -> None:
        self.running = False
        for service in self.services.values():
            self._stop_service(service)


def _load_services(config_path: Optional[Path]) -> Dict[str, dict]:
    if not config_path:
        return DEFAULT_SERVICES
    with config_path.open("r", encoding="utf-8") as fh:
        loaded = json.load(fh)
    if not isinstance(loaded, dict):
        raise ValueError("Service config must be a JSON object keyed by service name")
    return loaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EvezOS immortality watchdog")
    parser.add_argument("--config", type=Path, help="Optional JSON service config")
    parser.add_argument("--base-backoff", type=float, default=1.0)
    parser.add_argument("--max-backoff", type=float, default=60.0)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Root of evez-os repository",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    services = _load_services(args.config)
    watchdog = ImmortalityWatchdog(
        repo_root=args.repo_root,
        services=services,
        base_backoff=args.base_backoff,
        max_backoff=args.max_backoff,
        poll_interval=args.poll_interval,
    )

    def _handle_shutdown(signum: int, _frame: object) -> None:
        print(f"[watchdog] received signal {signum}, shutting down")
        watchdog.shutdown()

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    try:
        watchdog.loop()
    finally:
        watchdog.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
