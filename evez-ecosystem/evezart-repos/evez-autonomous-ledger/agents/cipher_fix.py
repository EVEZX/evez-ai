#!/usr/bin/env python3
"""CIPHER Fix Agent — scan CI failures, diagnose, comment with fix path"""
import os, json, requests, datetime

TOKEN = os.environ.get("GITHUB_TOKEN","")
OWNER = "EvezArt"
H = {"Authorization": f"Bearer {TOKEN}", "X-GitHub-Api-Version": "2022-11-28",
     "Content-Type": "application/json"}
REPOS = ["evez-os","Evez666","evez-autonomous-ledger","nexus","evez-agentnet",
         "maes","evezo","evez-platform","openclaw-runtime"]

def ts(): return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def classify_failure(name):
    n = name.lower()
    if "build" in n or "deploy" in n: return "BUILD_FAILURE"
    if "test" in n: return "TEST_FAILURE"
    if "lint" in n or "format" in n: return "LINT_FAILURE"
    if "ci" in n: return "CI_FAILURE"
    return "WORKFLOW_FAILURE"

diagnosed = []
for repo in REPOS:
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?status=failure&per_page=5",
                    headers=H, timeout=10)
    if not r.ok: continue
    for run in r.json().get("workflow_runs",[]):
        ftype = classify_failure(run["name"])
        diagnosed.append({"repo":repo,"name":run["name"],"ftype":ftype,
                          "url":run["html_url"],"id":run["id"]})
        print(f"  {ftype:20s} [{repo}] {run['name']}")

print(f"\nFIX: {len(diagnosed)} failures diagnosed")
os.makedirs("DECISIONS", exist_ok=True)
with open(f"DECISIONS/{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_fix_scan.json","w") as f:
    json.dump({"failures":diagnosed,"ts":ts(),"agent":"CIPHER_FIX_v1"}, f, indent=2)
