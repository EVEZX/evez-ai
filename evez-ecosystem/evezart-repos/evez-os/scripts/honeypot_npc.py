#!/usr/bin/env python3
"""
EVEZ-OS Honeypot NPC Classifier + Witness Registry Generator
Reads network intrusion events, enriches via BigDataCloud,
classifies via Groq LLM, publishes public Witness Registry HTML.
Data endpoint at /witness-registry/api/entities.json feeds VCL overlay.

Usage:
  python3 honeypot_npc.py [--input-file <honeypot.ndjson>] [--publish]
  
Env vars:
  BIG_DATA_CLOUD_KEY, PDL_API_KEY, GROQ_API_KEY, GITHUB_TOKEN
"""

import os, sys, json, time, hashlib, datetime, argparse, requests
from typing import Optional

BDC_KEY  = os.getenv("BIG_DATA_CLOUD_KEY", os.getenv("BDC_API_KEY", ""))
PDL_KEY  = os.getenv("PDL_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
PAGES_REPO = "EvezArt/evezart.github.io"
REGISTRY_PATH = "witness-registry"

ARCHETYPES = {
    "SCANNER":   {"icon": "🔍", "desc": "Automated port/vuln scanner",      "threat": "LOW"},
    "BOT":       {"icon": "🤖", "desc": "Script-driven request bot",         "threat": "MEDIUM"},
    "CRAWLER":   {"icon": "🕷️", "desc": "Aggressive web crawler",           "threat": "LOW"},
    "APT":       {"icon": "👹", "desc": "Advanced persistent threat actor",  "threat": "CRITICAL"},
    "BRUTE":     {"icon": "🔨", "desc": "Credential brute-force agent",      "threat": "HIGH"},
    "EXFIL":     {"icon": "📤", "desc": "Data exfiltration attempt",          "threat": "CRITICAL"},
    "PROBE":     {"icon": "📡", "desc": "Passive reconnaissance probe",       "threat": "LOW"},
    "AMPLIFIER": {"icon": "📢", "desc": "DDoS reflection amplifier",          "threat": "HIGH"},
    "UNKNOWN":   {"icon": "❓", "desc": "Unclassified intrusion signal",      "threat": "MEDIUM"},
}

THREAT_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

SAMPLE_EVENTS = [
    {"ip": "185.220.101.45", "ports": [22, 2222, 3389], "protocols": ["TCP"],
     "request_count": 847, "user_agents": [],
     "first_seen": "2026-06-06T00:00:00Z", "last_seen": "2026-06-07T18:00:00Z", "source": "honeypot_ssh"},
    {"ip": "45.129.56.0", "ports": [80, 443, 8080], "protocols": ["HTTP"],
     "request_count": 3200, "user_agents": ["Mozilla/5.0 (compatible; MJ12bot/v1.4.8)"],
     "first_seen": "2026-06-05T12:00:00Z", "last_seen": "2026-06-07T12:00:00Z", "source": "honeypot_web"},
    {"ip": "91.240.118.42", "ports": [80, 443, 5985, 1433], "protocols": ["HTTP", "TCP"],
     "request_count": 156, "user_agents": [],
     "first_seen": "2026-06-07T08:00:00Z", "last_seen": "2026-06-07T17:00:00Z", "source": "honeypot_network"},
    {"ip": "94.102.49.190", "ports": [6379, 27017, 5432, 3306], "protocols": ["TCP"],
     "request_count": 42, "user_agents": [],
     "first_seen": "2026-06-07T14:00:00Z", "last_seen": "2026-06-07T19:00:00Z", "source": "honeypot_db"},
]

def enrich_ip(ip):
    info = {"ip": ip, "country": "?", "city": "?", "org": "?", "asn": "?", "abuse_score": 0}
    if not BDC_KEY: return info
    try:
        r = requests.get("https://api.bigdatacloud.net/data/ip-geolocation-full",
            params={"ip": ip, "key": BDC_KEY}, timeout=8)
        d = r.json()
        info["country"] = d.get("country", {}).get("name", "?")
        info["city"] = d.get("city", "?")
        info["org"] = d.get("organisation", "?")
        asn = d.get("autonomousSystem", {})
        info["asn"] = f"AS{asn.get('asn','?')} {asn.get('organisation','')}"
        info["lat"] = d.get("location", {}).get("latitude")
        info["lon"] = d.get("location", {}).get("longitude")
        info["abuse_score"] = d.get("hazardReport", {}).get("score", 0)
    except Exception as e: print(f"[bdc] {ip} err: {e}")
    return info

def classify_with_llm(event, geo):
    fallback = {"archetype": "UNKNOWN", "confidence": 0.5,
        "npc_name": f"Wraith-{hashlib.md5(event['ip'].encode()).hexdigest()[:4].upper()}",
        "behavior_summary": "LLM unavailable", "npc_lore": ""}
    if not GROQ_KEY: return fallback
    prompt = f"""EVEZ-OS Witness Classifier. Analyze this network intrusion event.

EVENT: IP={event['ip']} ports={event.get('ports',[])} protocols={event.get('protocols',[])} requests={event.get('request_count','?')} ua={event.get('user_agents',[])} time={event.get('first_seen','?')} to {event.get('last_seen','?')}
GEO: {geo['country']}/{geo['city']} ASN={geo['asn']} abuse={geo['abuse_score']}
ARCHETYPES: {', '.join(ARCHETYPES.keys())}

Respond ONLY valid JSON: {{"archetype":"<archetype>","confidence":<0.0-1.0>,"npc_name":"<dramatic codename max 3 words>","behavior_summary":"<one sentence technical>","npc_lore":"<2 sentences cyber thriller flavor>"}}"""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],
                  "temperature":0.3,"max_tokens":300,"response_format":{"type":"json_object"}},
            timeout=15)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"[llm] {event['ip']} err: {e}"); return fallback

def render_html(entities):
    rows = ""
    for e in sorted(entities, key=lambda x: x.get("threat_rank", 99)):
        a = ARCHETYPES.get(e["archetype"], ARCHETYPES["UNKNOWN"])
        tc = {"CRITICAL":"#ff2d55","HIGH":"#ff9500","MEDIUM":"#ffcc00","LOW":"#34c759"}.get(a["threat"],"#8e8e93")
        rows += f'<tr class="entity-row" data-archetype="{e["archetype"]}"><td><span>{a["icon"]}</span> <strong>{e.get("npc_name","?")}</strong></td><td><code>{e["ip"]}</code></td><td>{e["archetype"]}</td><td style="color:{tc}">⬤ {a["threat"]}</td><td>{e.get("country","?")} · {e.get("city","?")}</td><td>{e.get("org","?")[:40]}</td><td>{e.get("behavior_summary","?")[:80]}</td><td>{str(e.get("first_seen","?"))[:10]}</td><td>{int(e.get("confidence",0)*100)}%</td></tr><tr><td colspan="9" style="padding:4px 16px 12px 40px;color:#7070a0;font-style:italic;font-size:11px">📜 {e.get("npc_lore","")}</td></tr>'
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(entities)
    crit = sum(1 for e in entities if ARCHETYPES.get(e.get("archetype","UNKNOWN"),{}).get("threat")=="CRITICAL")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EVEZ-OS Witness Registry</title><style>:root{{--bg:#0a0a0f;--s:#12121a;--b:#1e1e2e;--t:#e2e2ff;--m:#7070a0;--a:#7c3aed;--r:#ff2d55;--font:'SF Mono','JetBrains Mono','Courier New',monospace}}*{{box-sizing:border-box;margin:0;padding:0}}body{{background:var(--bg);color:var(--t);font-family:var(--font);font-size:13px}}header{{padding:24px 32px;border-bottom:1px solid var(--b);background:var(--s)}}h1{{font-size:22px;color:var(--a);letter-spacing:2px;text-transform:uppercase}}.meta{{color:var(--m);margin-top:4px;font-size:11px}}.stats{{display:flex;gap:32px;padding:16px 32px;background:var(--s);border-bottom:1px solid var(--b)}}.stat .val{{font-size:28px;font-weight:bold;color:var(--a)}}.stat.c .val{{color:var(--r)}}.stat .lbl{{font-size:10px;color:var(--m);text-transform:uppercase;letter-spacing:1px}}.badge{{display:inline-block;padding:2px 8px;background:var(--r);color:#fff;border-radius:4px;font-size:10px;animation:p 2s infinite}}@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}table{{width:100%;border-collapse:collapse}}th{{padding:10px 16px;text-align:left;color:var(--m);font-size:10px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid var(--b);position:sticky;top:0;background:var(--bg);z-index:10}}.entity-row td{{padding:12px 16px;border-bottom:1px solid var(--b)}}.entity-row:hover td{{background:var(--s)}}code{{background:var(--b);padding:2px 6px;border-radius:4px;color:#7dd3fc}}footer{{padding:24px 32px;color:var(--m);font-size:11px;border-top:1px solid var(--b)}}.data-link{{float:right;color:var(--m);font-size:11px;text-decoration:none}}.data-link:hover{{color:var(--a)}}</style></head><body><header><h1>⚡ EVEZ-OS Witness Registry <span class="badge">● LIVE</span></h1><div class="meta">Investigatory OSINT Classification · {total} entities · Updated {ts} <a class="data-link" href="api/entities.json">📡 JSON API</a></div></header><div class="stats"><div class="stat"><span class="val">{total}</span><span class="lbl">Entities</span></div><div class="stat c"><span class="val">{crit}</span><span class="lbl">Critical</span></div></div><div style="overflow-x:auto"><table><thead><tr><th>Codename</th><th>IP</th><th>Archetype</th><th>Threat</th><th>Location</th><th>Org</th><th>Behavior</th><th>First Seen</th><th>Conf</th></tr></thead><tbody>{rows}</tbody></table></div><footer>EVEZ-OS Witness Registry · Defense-only · Article XIII compliant · Network-level classification (IP/ASN/port) only</footer></body></html>"""

def publish_to_github_pages(entities, html):
    import base64
    if not GH_TOKEN:
        out = os.path.join(os.path.dirname(__file__), "../output/witness-registry")
        os.makedirs(out+"/api", exist_ok=True)
        open(out+"/index.html","w").write(html)
        open(out+"/api/entities.json","w").write(json.dumps({"entities":entities},indent=2))
        print(f"[pages] Written to {out}/")
        return
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}
    base_url = f"https://api.github.com/repos/{PAGES_REPO}/contents"
    def upsert(path, content, msg):
        full = f"{REGISTRY_PATH}/{path}"
        ex = requests.get(f"{base_url}/{full}", headers=headers, timeout=10).json()
        payload = {"message": msg, "content": base64.b64encode(content.encode()).decode()}
        if ex.get("sha"): payload["sha"] = ex["sha"]
        r = requests.put(f"{base_url}/{full}", headers=headers, json=payload, timeout=15)
        print(f"[pages] {'✅' if r.status_code in (200,201) else '❌'} {full} ({r.status_code})")
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    upsert("index.html", html, f"witness-registry: {len(entities)} entities {ts}")
    upsert("api/entities.json", json.dumps({"generated_at":ts,"entities":entities},indent=2), f"witness-registry: api {ts}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file"); parser.add_argument("--publish", action="store_true")
    parser.add_argument("--max-events", type=int, default=100)
    args = parser.parse_args()
    if args.input_file and os.path.exists(args.input_file):
        events = []
        with open(args.input_file) as f:
            for line in f:
                try: events.append(json.loads(line.strip()))
                except: pass
        events = events[:args.max_events]
    else:
        print("[main] Using sample data")
        events = SAMPLE_EVENTS
    entities = []
    for ev in events:
        ip = ev.get("ip","0.0.0.0")
        print(f"[process] {ip}")
        geo = enrich_ip(ip)
        clf = classify_with_llm(ev, geo)
        time.sleep(0.3)
        a = ARCHETYPES.get(clf.get("archetype","UNKNOWN"), ARCHETYPES["UNKNOWN"])
        entities.append({**ev, **geo, **clf, "threat": a["threat"],
            "threat_rank": THREAT_RANK.get(a["threat"],99),
            "classified_at": datetime.datetime.utcnow().isoformat()+"Z",
            "entity_id": hashlib.sha256(f"{ip}:{ev.get('first_seen','')}".encode()).hexdigest()[:16]})
        print(f"  → {clf.get('archetype')} | {clf.get('npc_name')} | {a['threat']}")
    html = render_html(entities)
    if args.publish: publish_to_github_pages(entities, html)
    else:
        out = os.path.join(os.path.dirname(__file__), "../output/witness-registry")
        os.makedirs(out+"/api", exist_ok=True)
        open(out+"/index.html","w").write(html)
        open(out+"/api/entities.json","w").write(json.dumps({"generated_at":datetime.datetime.utcnow().isoformat()+"Z","entities":entities},indent=2))
        print(f"[main] Preview at {out}/index.html — run --publish to go live")
    return entities

if __name__ == "__main__":
    main()
