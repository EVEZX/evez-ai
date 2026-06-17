"""Seed initial tasks into OpenTree and NATS"""
import sys
sys.path.insert(0, '/home/openclaw/.openclaw/workspace/agent-bridge')
from task_router import create_task

tasks = [
    ("TASK-001", "Audit all EVEZ Docker services and document API endpoints", "claw", "high"),
    ("TASK-002", "Set up inter-agent heartbeat cron on both boxes", "azra", "normal"),
    ("TASK-003", "Push evez-spine v1.1.0 to PyPI", "claw", "high"),
    ("TASK-004", "Build agent-bridge health monitor as systemd service", "azra", "normal"),
    ("TASK-005", "Document full EVEZ stack architecture in lord-evez666", "both", "normal"),
]

for tid, title, assigned, priority in tasks:
    result = create_task(tid, title, assigned, priority=priority)
    print(f"{tid}: {result}")
