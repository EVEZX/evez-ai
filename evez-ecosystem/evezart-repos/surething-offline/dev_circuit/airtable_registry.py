#!/usr/bin/env python3
"""EVEZ Airtable Dev Circuit Registry
Manages DEV_CIRCUIT_TASKS table — the source of truth for all circuit tasks.
Env: AIRTABLE_API_KEY, AIRTABLE_BASE_ID
"""
from __future__ import annotations
import argparse, json, os, sys
import requests
from datetime import datetime, timezone

API = "https://api.airtable.com/v0"
TABLE = "DEV_CIRCUIT_TASKS"

class AirtableRegistry:
    def __init__(self):
        self.key = os.environ.get("AIRTABLE_API_KEY", "")
        self.base = os.environ.get("AIRTABLE_BASE_ID", "")
        self.h = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        self._tid: str | None = None

    def _req(self, method, path, **kw):
        r = requests.request(method, f"{API}{path}", headers=self.h, timeout=30, **kw)
        if not r.ok: raise ValueError(f"{method} {path}: {r.status_code} {r.text[:200]}")
        return r.json()

    def table_id(self) -> str:
        if self._tid: return self._tid
        schema = self._req("GET", f"/meta/bases/{self.base}/tables")
        for t in schema.get("tables", []):
            if t["name"] == TABLE:
                self._tid = t["id"]; return self._tid
        return TABLE  # fallback: use name directly

    def add_task(self, task: dict) -> dict:
        tid = self.table_id()
        return self._req("POST", f"/{self.base}/{tid}", json={"fields": {
            "task_id": task.get("task_id", ""),
            "title": task.get("title", ""),
            "repo": task.get("repo", ""),
            "target_file": task.get("target_file", ""),
            "spec": task.get("spec", ""),
            "model": task.get("model", "groq"),
            "status": "pending",
            "branch": task.get("branch", "main"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, "typecast": True})

    def update_task(self, record_id: str, updates: dict) -> dict:
        tid = self.table_id()
        if updates.get("status") in ("deployed", "failed"):
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()
        return self._req("PATCH", f"/{self.base}/{tid}/{record_id}", json={"fields": updates, "typecast": True})

    def pending_tasks(self) -> list[dict]:
        tid = self.table_id()
        r = self._req("GET", f"/{self.base}/{tid}", params={"filterByFormula": "{status}='pending'", "sort[0][field]": "created_at", "sort[0][direction]": "asc"})
        return [{"_id": rec["id"], **rec["fields"]} for rec in r.get("records", [])]

if __name__ == "__main__":
    from circuit_runner import SAMPLE_TASKS
    p = argparse.ArgumentParser()
    p.add_argument("--seed", action="store_true", help="Seed initial tasks")
    p.add_argument("--list", action="store_true", help="List pending")
    args = p.parse_args()
    reg = AirtableRegistry()
    if args.seed:
        for t in SAMPLE_TASKS: print(reg.add_task(t))
    elif args.list:
        tasks = reg.pending_tasks()
        for t in tasks: print(f"  {t.get('task_id','?'):10} {t.get('title','?')}")
    else: p.print_help()
