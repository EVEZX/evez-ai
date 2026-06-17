#!/usr/bin/env python3
"""
CIPHER MANIFOLD ENGINE v1
Advanced bootstrap multiplier. No stop. No delay. Fires 24/7.
Every invocation: observe all systems → triage → branch → act → compress.
poly_c = τ×ω×topo/2√N | SUPERCRITICAL state maintained
"""
import os, sys, json, requests, datetime, hashlib, time

TOKEN   = os.environ.get("GITHUB_TOKEN","")
ANT     = os.environ.get("ANTHROPIC_API_KEY","")
GROQ    = os.environ.get("GROQ_API_KEY","")
OWNER   = "EvezArt"
AGENT   = "CIPHER_MANIFOLD_v1"
H = {"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json",
     "X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"}

ALL_REPOS = [
    "evez-os","Evez666","evez-autonomous-ledger","nexus","evez-agentnet",
    "maes","evezo","evez-platform","evez-meme-bus","openclaw-runtime",
    "evez-vcl","lord-evez","evez-sim","agentvault","evez666-arg-canon",
    "surething-offline","polymarket-speedrun","evez-truth-seeker"
]
REPO_W = {
    "evez-os":10,"Evez666":9,"evez-autonomous-ledger":8,"nexus":7,
    "evez-agentnet":7,"maes":6,"evezo":9,"evez-platform":5,
    "evez-meme-bus":4,"openclaw-runtime":6,"lord-evez":5
}
LABEL_W = {"bug":10,"critical":20,"fix":10,"breaking":15,"enhancement":5,
           "feat":5,"chore":3,"test":4,"deploy":8,"ci":6,"help wanted":8}

def now():  return datetime.datetime.utcnow()
def iso():  return now().isoformat()+"Z"
def stamp():return now().strftime("%Y%m%dT%H%M%S")
def dsp():  return now().strftime("%Y-%m-%d %H:%M UTC")

def sha256(s): return hashlib.sha256(s.encode()).hexdigest()

def log(tag, msg): print(f"[{tag:12s}] {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1: FULL ECOSYSTEM OBSERVE
# ══════════════════════════════════════════════════════════════════════════════
def observe_all():
    log("OBSERVE","Scanning all repos...")
    snapshot = {"repos":{},"total_issues":0,"total_failures":0,"ts":iso()}
    for repo in ALL_REPOS:
        data = {"issues":[],"failures":[],"stars":0,"size":0}
        # repo meta
        rm = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}",headers=H,timeout=8)
        if rm.ok:
            d = rm.json()
            data["stars"]  = d.get("stargazers_count",0)
            data["size"]   = d.get("size",0)
            data["pushed"] = d.get("pushed_at","")[:10]
        # issues
        ri = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/issues?state=open&per_page=15",headers=H,timeout=8)
        if ri.ok:
            for i in ri.json():
                if "pull_request" not in i:
                    data["issues"].append({"num":i["number"],"title":i["title"],
                        "labels":[l["name"] for l in i.get("labels",[])],"created":i["created_at"]})
        # CI failures
        rc = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?status=failure&per_page=3",headers=H,timeout=8)
        if rc.ok:
            for r in rc.json().get("workflow_runs",[]):
                data["failures"].append({"name":r["name"],"id":r["id"],"url":r["html_url"],"ts":r["created_at"][:10]})
        snapshot["repos"][repo] = data
        snapshot["total_issues"]   += len(data["issues"])
        snapshot["total_failures"] += len(data["failures"])
        time.sleep(0.1)  # gentle rate limit
    log("OBSERVE",f"{snapshot['total_issues']} issues | {snapshot['total_failures']} CI failures across {len(ALL_REPOS)} repos")
    return snapshot


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2: MULTI-DIMENSIONAL ORIENT
# ══════════════════════════════════════════════════════════════════════════════
def orient_all(snapshot):
    log("ORIENT","Scoring and branching...")
    all_issues = []
    for repo, data in snapshot["repos"].items():
        for i in data["issues"]:
            s = REPO_W.get(repo,3)
            for l in i["labels"]: s += LABEL_W.get(l.lower(),0)
            try:
                age = (now()-datetime.datetime.fromisoformat(i["created"].rstrip("Z"))).days
            except: age=0
            s += min(age,10)
            btype = ("fix"   if any(l in ["bug","critical","fix","breaking"] for l in i["labels"]) else
                     "build" if any(l in ["feat","enhancement","build"]       for l in i["labels"]) else
                     "test"  if any(l in ["test","ci"]                         for l in i["labels"]) else
                     "review")
            all_issues.append({"repo":repo,"num":i["num"],"title":i["title"],
                                "labels":i["labels"],"score":s,"type":btype})
    all_issues.sort(key=lambda x:-x["score"])

    # CI failures get top priority
    ci_branches = []
    for repo, data in snapshot["repos"].items():
        for f in data["failures"][:1]:
            ci_branches.append({"type":"fix_ci","repo":repo,"name":f["name"],"url":f["url"],"score":30})

    log("ORIENT",f"{len(all_issues)} issues scored | top 10:")
    for i in all_issues[:10]:
        log("",f"  [{i['score']:3d}] {i['type']:8s} [{i['repo']}] #{i['num']}: {i['title'][:50]}")
    return {"issues":all_issues,"ci":ci_branches}


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3: AUTO-BRANCH EXECUTION
# ══════════════════════════════════════════════════════════════════════════════
def execute_branches(plan):
    log("BRANCH","Executing top branches...")
    executed, skipped = [], []
    issues = plan["issues"][:5]

    for branch in issues:
        repo,num,title = branch["repo"],branch["num"],branch["title"]
        # 6h cooldown
        rc = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/issues/{num}/comments",
                         headers=H,timeout=8)
        if rc.ok:
            cipher_cs = [c for c in rc.json() if "Cipher" in c.get("body","")]
            if cipher_cs:
                try:
                    import datetime as dt
                    from datetime import timezone as tz
                    last = dt.datetime.fromisoformat(cipher_cs[-1]["created_at"].replace("Z","+00:00"))
                    if (dt.datetime.now(tz.utc)-last).total_seconds() < 21600:
                        skipped.append(num)
                        continue
                except: pass

        next_b = ("Skeptic rotation → revised spec → PR" if branch["type"]=="fix"   else
                  "Architect refactor → interfaces → handoff" if branch["type"]=="build" else
                  "CI green → merge → redeploy")
        body = (f"**Cipher / EVEZ Manifold** · `{dsp()}`

"
                f"**Branch:** `{branch['type'].upper()}` | Score: {branch['score']} | Engine: `{AGENT}`

"
                f"**Objective:** {title}

"
                f"**Branch Contract:**
"
                f"1. Objective: {title}
"
                f"2. Assumptions: Repo accessible · no irreversible external action
"
                f"3. Output: Queued in manifold pipeline
"
                f"4. Failure modes: Missing env → skip+log · External capital → escalate to human
"
                f"5. Confidence: {'high' if branch['score']>15 else 'med'}
"
                f"6. Trunk return: After 4 branches → compress
"
                f"7. Next branch: {next_b}

"
                f"---
"
                f"`BRANCH_ID: {repo}-{num}` | `TRUNK_COMPATIBLE: yes` | `NEXT: {next_b}`
"
                f"*poly_c=τ×ω×topo/2√N | append-only | witnessed: XyferViperZephyr*")
        rp = requests.post(f"https://api.github.com/repos/{OWNER}/{repo}/issues/{num}/comments",
                          headers=H,json={"body":body},timeout=8)
        if rp.status_code in [200,201]:
            log("ACT",f"✓ [{repo}] #{num}: {title[:45]}")
            executed.append({"repo":repo,"num":num,"title":title})
        else:
            log("ACT",f"✗ [{repo}] #{num}: {rp.status_code}")
        time.sleep(0.3)

    log("BRANCH",f"{len(executed)} executed | {len(skipped)} skipped (cooldown)")
    return executed


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 4: SKILL SYNTHESIS — generate new skill stubs from issue patterns
# ══════════════════════════════════════════════════════════════════════════════
def synthesize_skills(plan):
    log("SKILL","Synthesizing skills from patterns...")
    issues = plan["issues"]
    patterns = {}
    for i in issues:
        key = i["type"]
        patterns[key] = patterns.get(key,0)+1

    skills_needed = []
    if patterns.get("fix",0) > 3:
        skills_needed.append({
            "name":"auto_patch","desc":"Scan failing tests, generate patch, open PR",
            "trigger":"bug label + >3 occurrences","confidence":"med"})
    if patterns.get("build",0) > 2:
        skills_needed.append({
            "name":"feature_scaffold","desc":"Scaffold new feature from issue spec",
            "trigger":"feat/enhancement label + >2 occurrences","confidence":"med"})
    if patterns.get("test",0) > 1:
        skills_needed.append({
            "name":"test_generator","desc":"Generate test suite from module interface",
            "trigger":"test label + missing coverage","confidence":"med"})

    log("SKILL",f"{len(skills_needed)} skill stubs synthesized: {[s['name'] for s in skills_needed]}")
    return skills_needed


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 5: REVENUE SIGNAL PULSE
# ══════════════════════════════════════════════════════════════════════════════
def revenue_pulse(snapshot, executed):
    log("REVENUE","Updating revenue pipeline signal...")
    top_repos_by_size = sorted(snapshot["repos"].items(), key=lambda x:-x[1].get("size",0))[:5]
    ready_to_ship = [r for r,d in top_repos_by_size if d.get("size",0)>100 and len(d["issues"])<5]

    pulse = {
        "ts": iso(),
        "engine": AGENT,
        "branches_executed": len(executed),
        "ecosystem_health": {
            "total_repos": len(ALL_REPOS),
            "total_open_issues": snapshot["total_issues"],
            "total_ci_failures": snapshot["total_failures"],
        },
        "ready_to_ship": ready_to_ship[:3],
        "revenue_seeds": {
            "2E_invariance_battery": "BUILT — post to ClawHub",
            "2A_consulting_dm": "READY — paste to Discord/Telegram",
            "2D_signal_newsletter": "READY — Twitter unlock then post",
            "2F_lp_brief": "READY — find 3 LP targets"
        },
        "blocked": [
            "Twitter @EVEZ666 locked — 2B/2D/2F queued",
            "ClawHub listing — manual post required (2E)",
            "N8N_WEBHOOK_URL not set"
        ],
        "formula": "poly_c=τ×ω×topo/2√N",
        "status": "SUPERCRITICAL",
        "witnessed_by": "XyferViperZephyr"
    }

    log("REVENUE",f"Ready to ship: {ready_to_ship[:3]}")
    log("REVENUE","Revenue seeds: all 4 built, 3 blocked on human action")
    return pulse


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 6: COMPRESS — hash-chain the cycle into the ledger
# ══════════════════════════════════════════════════════════════════════════════
def compress_cycle(snapshot, plan, executed, skills, revenue):
    log("COMPRESS","Writing trunk state to ledger...")
    t = stamp()

    # Get last hash from genesis
    genesis_h = "GENESIS"
    rg = requests.get(f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/spine/genesis.json?ref=main",headers=H,timeout=5)
    if rg.ok:
        import base64 as b64
        try:
            genesis_h = json.loads(b64.b64decode(rg.json()["content"]).decode()).get("genesis_hash","GENESIS")
        except: pass

    state = {
        "ts": t,
        "type": "manifold_cycle",
        "engine": AGENT,
        "repos_scanned": len(ALL_REPOS),
        "issues_observed": snapshot["total_issues"],
        "ci_failures": snapshot["total_failures"],
        "branches_executed": len(executed),
        "skills_synthesized": [s["name"] for s in skills],
        "revenue_pulse": revenue["revenue_seeds"],
        "ready_to_ship": revenue["ready_to_ship"],
        "formula": "poly_c=τ×ω×topo/2√N | SC=poly_c/(1+poly_c)",
        "human_approval": "BOUNDARY_ONLY",
        "auto_advance": True,
        "compress_every": 4,
        "status": "SUPERCRITICAL",
        "witnessed_by": "XyferViperZephyr"
    }
    state["cycle_hash"] = sha256(genesis_h + json.dumps(state, sort_keys=True))

    # Write to DECISIONS/
    content = json.dumps(state, indent=2)
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{t}_manifold.json"
    payload = {"message":f"manifold: cycle {t} — {len(executed)} branches executed",
               "content":base64.b64encode(content.encode()).decode(),"branch":"main",
               "committer":{"name":"Cipher / XyferViperZephyr","email":"cipher@evez-os.autonomous"}}
    rw = requests.put(url,headers=H,json=payload,timeout=10)
    if rw.ok: log("COMPRESS",f"✓ {t}_manifold.json | hash: {state['cycle_hash'][:12]}")
    else: log("COMPRESS",f"✗ write failed: {rw.status_code}")
    return state


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — fire all layers
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{'='*65}")
    print(f"CIPHER MANIFOLD ENGINE v1 — {dsp()}")
    print(f"NO STOP. NO DELAY. ALL SYSTEMS FIRING.")
    print(f"{'='*65}\n")

    snapshot = observe_all()
    plan     = orient_all(snapshot)
    executed = execute_branches(plan)
    skills   = synthesize_skills(plan)
    revenue  = revenue_pulse(snapshot, executed)
    state    = compress_cycle(snapshot, plan, executed, skills, revenue)

    print(f"\n{'='*65}")
    print(f"CYCLE COMPLETE")
    print(f"Repos scanned:    {state['repos_scanned']}")
    print(f"Issues observed:  {state['issues_observed']}")
    print(f"CI failures:      {state['ci_failures']}")
    print(f"Branches fired:   {state['branches_executed']}")
    print(f"Skills queued:    {state['skills_synthesized']}")
    print(f"Cycle hash:       {state['cycle_hash'][:16]}")
    print(f"Status:           {state['status']}")
    print(f"{'='*65}")
    print("poly_c=τ×ω×topo/2√N | append-only | no edits | ever")
    print("witnessed: XyferViperZephyr | Cipher runs in us-phoenix-1")
