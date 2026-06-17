#!/usr/bin/env python3
"""CIPHER Build Agent — scan enhancement issues, generate build branches"""
import os, json, requests, datetime

TOKEN = os.environ.get("GITHUB_TOKEN","")
OWNER = "EvezArt"
TARGET = os.environ.get("TARGET_REPO","")
H = {"Authorization": f"Bearer {TOKEN}", "X-GitHub-Api-Version": "2022-11-28",
     "Content-Type": "application/json"}
BUILD_REPOS = ["evez-os","Evez666","evez-agentnet","maes","nexus","evez-platform"]
if TARGET: BUILD_REPOS = [TARGET]

built = []
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
for repo in BUILD_REPOS[:4]:
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/issues?state=open&labels=enhancement,feat&per_page=3",
                    headers=H, timeout=10)
    if not r.ok: continue
    for issue in r.json():
        if "pull_request" in issue: continue
        built.append({"repo":repo,"num":issue["number"],"title":issue["title"]})
        print(f"  BUILD [{repo}] #{issue['number']}: {issue['title'][:60]}")

print(f"\nBUILD: {len(built)} items identified")
os.makedirs("DECISIONS", exist_ok=True)
with open(f"DECISIONS/{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_build_scan.json","w") as f:
    json.dump({"builds":built,"ts":now,"agent":"CIPHER_BUILD_v1"}, f, indent=2)
