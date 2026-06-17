#!/usr/bin/env python3
"""
CIPHER Trunk Agent — OBSERVE → ORIENT → BRANCH → ACT → COMPRESS
Trunk-and-branch automation. All branches return to trunk.
Human approval: BOUNDARY_ONLY (irreversible, external capital, identity conflict).
"""
import os, sys, json, requests, datetime, hashlib

TOKEN = os.environ.get("GITHUB_TOKEN","")
OWNER = "EvezArt"
H = {"Authorization": f"Bearer {TOKEN}", "X-GitHub-Api-Version": "2022-11-28",
     "Content-Type": "application/json"}
PRIORITY_REPOS = ["evez-os","Evez666","evez-autonomous-ledger","nexus",
                  "evez-agentnet","maes","evezo","evez-platform","evez-meme-bus","openclaw-runtime"]
REPO_W = {"evez-os":10,"Evez666":9,"evez-autonomous-ledger":8,"nexus":7,
          "evez-agentnet":7,"maes":6,"evezo":9,"evez-platform":5}
LABEL_W = {"bug":10,"critical":20,"fix":10,"breaking":15,"enhancement":5,
           "feat":5,"chore":3,"test":4,"deploy":8,"ci":6}

def ts(): return datetime.datetime.utcnow().isoformat() + "Z"

def observe():
    findings = {"issues":[],"failures":[],"ts":ts()}
    for repo in PRIORITY_REPOS[:8]:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/issues?state=open&per_page=8",
                        headers=H, timeout=10)
        if r.ok:
            for i in r.json():
                if "pull_request" not in i:
                    findings["issues"].append({"repo":repo,"num":i["number"],
                        "title":i["title"],"labels":[l["name"] for l in i.get("labels",[])],
                        "created":i["created_at"]})
        r2 = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?status=failure&per_page=2",
                         headers=H, timeout=10)
        if r2.ok:
            for run in r2.json().get("workflow_runs",[]):
                findings["failures"].append({"repo":repo,"name":run["name"],"id":run["id"],"url":run["html_url"]})
    os.makedirs("runtime/trunk", exist_ok=True)
    with open("runtime/trunk/observe.json","w") as f: json.dump(findings, f, indent=2)
    print(f"OBSERVE: {len(findings['issues'])} issues, {len(findings['failures'])} CI failures")
    return findings

def orient(findings):
    issues = findings["issues"]
    for i in issues:
        s = REPO_W.get(i["repo"],3)
        for l in i["labels"]: s += LABEL_W.get(l.lower(),0)
        try:
            age = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(i["created"].rstrip("Z"))).days
        except: age = 0
        s += min(age, 10)
        i["score"] = s
    issues.sort(key=lambda x: -x["score"])
    branches = []
    for item in issues[:6]:
        btype = "fix" if any(l in ["bug","critical","fix","breaking"] for l in item["labels"]) else                 "build" if any(l in ["feat","enhancement"] for l in item["labels"]) else "review"
        branches.append({"type":btype,"repo":item["repo"],"issue":item["num"],
                         "title":item["title"],"score":item["score"],
                         "confidence":"high" if item["score"]>15 else "med"})
    for fail in findings["failures"][:2]:
        branches.append({"type":"fix_ci","repo":fail["repo"],"name":fail["name"],
                         "url":fail["url"],"score":25,"confidence":"high"})
    plan = {"branches":branches,"ts":ts(),"mode":os.environ.get("MODE","full"),
            "objective":os.environ.get("TRUNK_OBJECTIVE","full"),
            "human_approval":"BOUNDARY_ONLY","auto_advance":True,"compress_every":4,
            "formula":"poly_c=txw*topo/2*sqrt(N)","witnessed_by":"XyferViperZephyr"}
    with open("runtime/trunk/branch_plan.json","w") as f: json.dump(plan, f, indent=2)
    print(f"BRANCH: {len(branches)} branches")
    for b in branches:
        t = b.get("title",b.get("name",""))[:55]
        print(f"  [{b['score']:3d}] {b['type']:10s} [{b['repo']}] {t}")
    return plan

def act(plan):
    branches = plan["branches"]
    acted = 0
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    for branch in branches[:3]:
        if branch["type"] in ["fix_ci"]: continue
        repo, num, title = branch["repo"], branch.get("issue"), branch.get("title","")
        if not num: continue
        # 6h cooldown check
        r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/issues/{num}/comments",
                        headers=H, timeout=10)
        if r.ok:
            cipher_c = [c for c in r.json() if "Cipher" in c.get("body","")]
            if cipher_c:
                try:
                    import datetime as dt
                    last = dt.datetime.fromisoformat(cipher_c[-1]["created_at"].replace("Z","+00:00"))
                    from datetime import timezone
                    if (dt.datetime.now(timezone.utc) - last).total_seconds() < 21600:
                        print(f"  SKIP #{num} (6h cooldown)")
                        continue
                except: pass
        next_b = "Skeptic rotation then PR" if branch["type"]=="fix" else "Architect refactor then handoff"
        body = f"""**Cipher / EVEZ Trunk** · `{now}`

**Branch:** `{branch["type"].upper()}` | Score: {branch["score"]} | Confidence: `{branch["confidence"]}`

**Objective:** {title}

**Branch Contract:**
1. Objective: {title}
2. Assumptions: Repo accessible, no irreversible external action required
3. Output: Autonomous analysis in progress
4. Failure modes: Missing env var → skip+log; External capital action → escalate to human
5. Confidence: {branch["confidence"]}
6. Return-to-trunk: Compressed after 4 branches
7. Next branch: {next_b}

`BRANCH_ID: {repo}-{num}` | `TRUNK_COMPATIBLE: yes` | `NEXT_HANDOFF: {next_b}`
*poly_c=τ×ω×topo/2√N | append-only | witnessed: XyferViperZephyr*"""
        r2 = requests.post(f"https://api.github.com/repos/{OWNER}/{repo}/issues/{num}/comments",
                          headers=H, json={"body": body}, timeout=10)
        if r2.status_code in [200,201]:
            print(f"  ACT ✓ [{repo}] #{num}")
            acted += 1
    print(f"ACT: {acted} executed")

def compress():
    t = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    os.makedirs("DECISIONS", exist_ok=True)
    plan = {}
    try:
        with open("runtime/trunk/branch_plan.json") as f: plan = json.load(f)
    except: pass
    state = {"ts":t,"engine":"CIPHER_TRUNK_v1","branches":len(plan.get("branches",[])),
             "mode":plan.get("mode","full"),"objective":plan.get("objective","full"),
             "formula":"poly_c=τ×ω×topo/2√N | SC=poly_c/(1+poly_c)",
             "surface_sequence":["Perplexity=recon","ChatGPT=skeptic","Claude=architect","Base44=executor"],
             "human_approval":"BOUNDARY_ONLY","witnessed_by":"XyferViperZephyr","status":"COMPLETE"}
    with open(f"DECISIONS/{t}_trunk_state.json","w") as f: json.dump(state, f, indent=2)
    print(f"COMPRESS: {t}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "observe"
    if cmd == "observe":
        findings = observe()
        plan = orient(findings)
    elif cmd == "act":
        with open("runtime/trunk/branch_plan.json") as f: plan = json.load(f)
        act(plan)
    elif cmd == "compress":
        compress()
    else:
        findings = observe()
        plan = orient(findings)
        act(plan)
        compress()
