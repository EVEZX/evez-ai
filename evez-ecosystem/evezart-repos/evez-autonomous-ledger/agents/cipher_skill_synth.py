#!/usr/bin/env python3
"""
CIPHER SKILL SYNTH — EVEZ-OS Skill Discovery & Auto-Integration
Scans evez-skills repo, indexes new skills, appends FIRE events for significant discoveries.
Runs as part of unified_daily cycle. No LLM required — pure structural analysis.
"""
import os, json, hashlib, datetime, sys, urllib.request, urllib.error

GITHUB_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
SKILLS_REPO = "EvezArt/evez-skills"
LEDGER_REPO = "EvezArt/evez-autonomous-ledger"
SPINE_FILE = "spine/skill_synth.jsonl"

def ts():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gh_get(path):
    url = f"https://api.github.com/repos/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    print(f"\n{'='*60}")
    print(f"CIPHER SKILL SYNTH // {ts()}")
    print(f"{'='*60}")

    # Scan evez-skills
    items = gh_get(f"{SKILLS_REPO}/contents/skills")
    if "error" in items or not isinstance(items, list):
        print(f"⚠ Could not fetch skills: {items}")
        skill_names = []
    else:
        skill_names = [i["name"] for i in items if i["type"] == "dir"]
        print(f"\n📦 Found {len(skill_names)} skills in {SKILLS_REPO}:")
        for s in skill_names:
            print(f"   • {s}")

    # Analyze skill categories
    categories = {
        "finance": [s for s in skill_names if any(x in s for x in ["finance","stock","crypto","tax","revenue","profit","payment","defi","algo-risk","bloom","credit","real-estate"])],
        "ai": [s for s in skill_names if any(x in s for x in ["agent","ai","debug","systematic","production"])],
        "data": [s for s in skill_names if any(x in s for x in ["pdf","excel","docx","xlsx","pptx","scraping","analytics"])],
        "search": [s for s in skill_names if any(x in s for x in ["finder","search","internet","web","apify"])],
    }

    print(f"\n📊 Skill Categories:")
    for cat, skills in categories.items():
        print(f"   {cat}: {len(skills)} — {', '.join(skills[:3])}{'...' if len(skills)>3 else ''}")

    # Build spine event
    event = {
        "id": f"SKILL-SYNTH-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "type": "SKILL_DISCOVERY",
        "timestamp": ts(),
        "payload": {
            "total_skills": len(skill_names),
            "skills": skill_names,
            "categories": {k: len(v) for k,v in categories.items()},
            "repo": SKILLS_REPO
        }
    }
    event["hash"] = sha256(json.dumps(event, sort_keys=True))

    # Append to local spine log
    os.makedirs("spine", exist_ok=True)
    with open(SPINE_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"\n✅ Spine event: {event['id']}")
    print(f"   hash: {event['hash'][:24]}...")

    # Summary
    print(f"\n{'='*60}")
    print(f"SKILL SYNTH COMPLETE")
    print(f"Total skills indexed: {len(skill_names)}")
    print(f"Categories: {', '.join(f'{k}={len(v)}' for k,v in categories.items())}")
    print(f"Spine: {SPINE_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
