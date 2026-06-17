#!/usr/bin/env python3
"""
Tier 2/3: watch loop runner

Runs a probe on an interval and appends to spine.
Designed to be used:
  - interactively (Ctrl-C to stop)
  - from cron/systemd timers
"""
from __future__ import annotations
import time
from typing import Callable, Dict, Any

def watch(run_fn: Callable[[], Dict[str, Any]], interval_s: int = 60, jitter_s: int = 0):
    n = 0
    while True:
        n += 1
        run_fn()
        sleep = interval_s + (jitter_s if jitter_s else 0)
        time.sleep(max(1, sleep))
