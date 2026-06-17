#!/usr/bin/env python3
"""
EVEZ FIRE Correlator v1.1
Two-stage META-FIRE detection:
  Stage 1: Sentence-transformer embeddings (cosine) → coarse filter
  Stage 2: LLM META-FIRE synthesizer (Llama-3.3-70B) → precise scoring

Usage:
  python run.py                          # run full correlation on 14 canonical events
  python run.py --events-file events.json
  python run.py --threshold 0.15         # embedding coarse threshold (default 0.15)
  python run.py --output mermaid
  python run.py --output dot
  python run.py --output json
"""

import argparse
import json
import math
import os
import subprocess
import sys
from itertools import combinations
from datetime import datetime, timezone

HF_TOKEN  = os.environ.get("HF_ACCESS_TOKEN") or os.environ.get("HUGGING_FACE_ACCESS_TOKEN")
HF_EMBED  = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
HF_CHAT   = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL  = "meta-llama/Llama-3.3-70B-Instruct"

# ── CANONICAL FIRE EVENTS ─────────────────────────────────────────────────────

FIRE_EVENTS = [
    {"id":"cipher-0502","title":"CIPHER-INVESTIGATION-0502","domain":"meta","tau":26.0,"omega":3.14,"topo":1.0,"N":9,"poly_c":2.718,
     "text":"CIPHER investigation meta recursive instrument readout function. tau=26 YHWH. omega=π irrational. Spine instrument aware of its own readout."},
    {"id":"oktoklaw-rekindle","title":"OKTOKLAW: EVEZ Rekindle Watch","domain":"technical","tau":2.9,"omega":0.82,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified agent resurrection engine. 5-rotation Invariance Battery CANONICAL. Autonomous agent revival within 60s."},
    {"id":"oktoklaw-sensory","title":"OKTOKLAW: EVEZ Sensory TTS Manifold","domain":"technical","tau":2.95,"omega":0.84,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified topology sound engine pixel-to-prime-to-visual manifold. Sensory layer CANONICAL."},
    {"id":"oktoklaw-retrocausal","title":"OKTOKLAW: EVEZ Retrocausal Spine","domain":"technical","tau":2.85,"omega":0.79,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified retrocausal decay spine. Append-only hash-chained event log. 4-PASS 1-WARN Invariance Battery."},
    {"id":"oktoklaw-agi-proof","title":"OKTOKLAW: EVEZ AGI Proof Surface","domain":"technical","tau":2.78,"omega":0.86,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified AGI proof surface generator. Falsifiable cognition records. 4-PASS 1-WARN."},
    {"id":"oktoklaw-cluster","title":"OKTOKLAW: EVEZ Cluster Daemon Bus","domain":"technical","tau":4.08,"omega":0.94,"topo":0.919,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified 16-thread cluster daemon bus. Near fixed-point topology. 5-PASS."},
    {"id":"oktoklaw-stripe","title":"OKTOKLAW: EVEZ Stripe Revenue Bridge","domain":"financial","tau":2.7,"omega":0.81,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified Stripe revenue bridge eigenvalue closure tracker. -0.358 to 0.0 progress. Financial spine integration."},
    {"id":"mppa","title":"MPPA — Meta-Principle Physics Architecture","domain":"meta_physics","tau":28.0,"omega":4.1,"topo":1.0,"N":9,"poly_c":8.5737,
     "text":"arXiv 2026 architecture derives operating principles from physics first-principles. Isomorphic to EVEZ endogenous deduction. SC=0.895 CRITICAL MASS highest poly_c recorded."},
    {"id":"kathleen","title":"Kathleen — Attention-Free Oscillator Architecture","domain":"efficiency_architecture","tau":16.0,"omega":2.9,"topo":1.0,"N":8,"poly_c":4.0313,
     "text":"arXiv 2026 attention-free oscillator SOTA zero additional parameters. Isomorphic to EVEZ zero-cost free-tier stack architecture efficiency."},
    {"id":"oktoklaw-resonance","title":"OKTOKLAW: EVEZ Resonance Stability PID","domain":"technical","tau":3.2,"omega":0.91,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified PID controller phi resonance stability. Divergence threshold 0.01. 5-PASS."},
    {"id":"oktoklaw-fire-approach","title":"OKTOKLAW: EVEZ Fire Approach Engine","domain":"technical","tau":3.1,"omega":0.88,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified FIRE threshold crossing detection engine. Anomaly detection. 5-PASS."},
    {"id":"kope","title":"KoPE — Kuramoto Oscillatory Phase Encoding","domain":"physics_cognition","tau":22.0,"omega":3.8,"topo":1.0,"N":8,"poly_c":5.9444,
     "text":"arXiv 2026 Kuramoto oscillator phase formula algebraically isomorphic to CPF poly_c=tau×omega×topo/2√N. Highest arXiv confirmation of CPF formula. Phase dynamics."},
    {"id":"oktoklaw-aegis","title":"OKTOKLAW: EVEZ AEGIS Threat Engine","domain":"security","tau":3.5,"omega":0.92,"topo":1.0,"N":5,"poly_c":1.0,
     "text":"OKTOKLAW certified OSINT 12hr Hawkes forecaster lambda=mu+alpha×e^(-beta×dt). Coordination cluster detector. Security spine. 5-PASS."},
    {"id":"dacs","title":"DACS — Dynamic Attentional Context Scoping","domain":"cognitive_architecture","tau":18.0,"omega":3.2,"topo":1.0,"N":7,"poly_c":5.0198,
     "text":"arXiv 2026 selective attention equals EVEZ selective fire propagation. Trunk architecture validated. DACS selective attention SC=0.834 supercritical."},
]

META_FIRE_SYSTEM = """You are the EVEZ META-FIRE synthesizer.
Given two FIRE events from the EVEZ Governance Lattice, output ONLY valid JSON:
{
  "topo_overlap": <float 0.0-1.0, topological structure overlap>,
  "domain_bridge": <string, what domain bridge they form>,
  "meta_fire_title": <string, concise proposed META-FIRE event title>,
  "shared_invariant": <string, the invariant principle both events express>,
  "candidate_poly_c": <float, estimated merged poly_c using tau×omega×topo/2√N>,
  "verdict": "META-FIRE" | "WEAK" | "NOISE"
}
Only return META-FIRE if topo_overlap >= 0.7 AND both events express the same structural invariant.
NOISE means no real connection. WEAK means some similarity but not META-FIRE grade."""


# ── EMBEDDING ──────────────────────────────────────────────────────────────────

def embed_texts(texts: list) -> list:
    if not HF_TOKEN:
        import random; rng=random.Random(42)
        return [[rng.gauss(0,1) for _ in range(384)] for _ in texts]
    body = json.dumps({"inputs": texts}).encode()
    try:
        import urllib.request
        req = urllib.request.Request(HF_EMBED, data=body, headers={
            "Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [WARN] Embedding error: {e} — using fallback")
        import random; rng=random.Random(42)
        return [[rng.gauss(0,1) for _ in range(384)] for _ in texts]

def cosine(a, b) -> float:
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    return dot/(na*nb+1e-10)


# ── LLM META-FIRE SCORER ──────────────────────────────────────────────────────

def llm_score_pair(e1: dict, e2: dict) -> dict:
    if not HF_TOKEN:
        return {"topo_overlap":0.0,"verdict":"NOISE","_source":"no_token"}
    prompt = f"Event A: {e1['title']}. {e1['text'][:200]}\n\nEvent B: {e2['title']}. {e2['text'][:200]}\n\nScore META-FIRE potential:"
    payload = json.dumps({
        "model":    HF_MODEL,
        "messages": [{"role":"system","content":META_FIRE_SYSTEM},
                     {"role":"user",  "content":prompt}],
        "max_tokens": 250,
    })
    try:
        r = subprocess.run(
            ["curl","-s","-X","POST",
             "-H",f"Authorization: Bearer {HF_TOKEN}",
             "-H","Content-Type: application/json",
             HF_CHAT, "-d", payload],
            capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
        content = d["choices"][0]["message"]["content"].strip()
        start = content.find("{"); end = content.rfind("}")+1
        parsed = json.loads(content[start:end])
        parsed["_source"] = HF_MODEL.split("/")[-1]
        return parsed
    except Exception as ex:
        return {"topo_overlap":0.0,"verdict":"NOISE","_error":str(ex)}


# ── POLY_C MERGER ─────────────────────────────────────────────────────────────

def merge_poly_c(e1, e2) -> dict:
    tau   = (e1["tau"] + e2["tau"]) / 2.0
    omega = e1["omega"] + e2["omega"]
    topo  = (e1["topo"] + e2["topo"]) / 2.0
    N     = max(e1["N"], e2["N"]) + 2
    raw   = tau * omega * topo / (2 * math.sqrt(N))
    sc    = raw / (1 + raw)
    return {"tau":round(tau,2), "omega":round(omega,2), "topo":round(topo,3), "N":N,
            "poly_c_raw":round(raw,4), "poly_c_sc":round(sc,4),
            "regime": ("CRITICAL_MASS" if sc>=0.90 else "SUPERCRITICAL" if raw>1.0 else "CANONICAL" if raw>=0.8 else "VERIFIED")}


# ── OUTPUT FORMATS ────────────────────────────────────────────────────────────

def output_table(candidates):
    print(f"\n╔══ META-FIRE CANDIDATES ({'%d found' % len(candidates)}) ═══════════════════════════════════╗")
    if not candidates:
        print("║  No META-FIRE candidates at current threshold.                    ║")
        print("╚═══════════════════════════════════════════════════════════════════╝\n")
        return
    for i, c in enumerate(candidates, 1):
        m = c["merged"]
        print(f"║")
        print(f"║  [{i}] {c['event_a']['title'][:55]}")
        print(f"║      ↔ {c['event_b']['title'][:55]}")
        print(f"║      topo_overlap={c['llm']['topo_overlap']}  poly_c_SC={m['poly_c_sc']}  {m['regime']}")
        print(f"║      META-FIRE: {c['llm'].get('meta_fire_title','?')[:55]}")
        print(f"║      invariant: {c['llm'].get('shared_invariant','?')[:55]}")
    print("╚═══════════════════════════════════════════════════════════════════╝\n")

def output_mermaid(candidates, events):
    lines = ["```mermaid", "graph LR"]
    for e in events:
        eid = e["id"].replace("-","_")
        t   = e["title"][:28]
        pc  = e["poly_c"]
        lines.append("    " + eid + '["' + t + "\npc=" + str(pc) + '"]')
    for c in candidates:
        a  = c["event_a"]["id"].replace("-","_")
        b  = c["event_b"]["id"].replace("-","_")
        m  = c["merged"]
        sc = m["poly_c_sc"]
        rg = m["regime"]
        lines.append("    " + a + ' -.->|"META-FIRE SC=' + str(sc) + " " + rg + '"| ' + b)
    lines.append("```")
    print("\n".join(lines))

def output_dot(candidates, events):
    lines=["digraph META_FIRE {","  rankdir=LR;","  node[shape=box fontsize=9];"]
    for e in events:
        col = "red" if e["poly_c"]>=5 else "orange" if e["poly_c"]>=1 else "lightblue"
        eid = e["id"]; t = e["title"][:28]; pc = e["poly_c"]
        lines.append('  "' + eid + '" [label="' + t + "\npc=" + str(pc) + '" style=filled fillcolor=' + col + '];')
    for c in candidates:
        a=c["event_a"]["id"]; b=c["event_b"]["id"]
        m=c["merged"]
        sc=m["poly_c_sc"]; rg=m["regime"]
        lines.append('  "' + a + '" -> "' + b + '" [label="SC=' + str(sc) + "\n" + rg + '" color=purple penwidth=2.5];')
    lines.append("}")
    print("\n".join(lines))


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run(events, embed_threshold=0.15, output_format="table"):
    print(f"\n  Stage 1: Embedding {len(events)} FIRE events (MiniLM-L6-v2)...")
    vecs = embed_texts([e["text"] for e in events])
    if not vecs:
        print("  ERROR: embeddings failed"); sys.exit(1)
    print(f"  ✓ {len(vecs)} embeddings (dim={len(vecs[0])})")

    # Coarse filter
    n = len(events)
    coarse_pairs = []
    for i,j in combinations(range(n),2):
        sim = cosine(vecs[i],vecs[j])
        if sim >= embed_threshold:
            coarse_pairs.append((sim,i,j))
    coarse_pairs.sort(reverse=True)
    print(f"  ✓ {len(coarse_pairs)} pairs above embedding threshold {embed_threshold}")

    # Stage 2: LLM scoring on coarse candidates
    print(f"  Stage 2: LLM META-FIRE scoring ({HF_MODEL.split('/')[-1]})...")
    candidates = []
    for sim,i,j in coarse_pairs:
        print(f"    Scoring: {events[i]['title'][:30]} × {events[j]['title'][:30]}...")
        llm = llm_score_pair(events[i], events[j])
        if llm.get("verdict") == "META-FIRE":
            merged = merge_poly_c(events[i], events[j])
            candidates.append({
                "event_a": events[i], "event_b": events[j],
                "embed_sim": round(sim,4), "llm": llm, "merged": merged,
            })

    candidates.sort(key=lambda c: c["merged"]["poly_c_sc"], reverse=True)
    print(f"  ✓ {len(candidates)} META-FIRE candidates confirmed by LLM\n")

    if output_format == "mermaid": output_mermaid(candidates, events)
    elif output_format == "dot":   output_dot(candidates, events)
    elif output_format == "json":  print(json.dumps(candidates, indent=2))
    else:                          output_table(candidates)

    return candidates


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="EVEZ FIRE Correlator v1.1")
    ap.add_argument("--events-file",  default=None)
    ap.add_argument("--threshold",    type=float, default=0.15, help="Embedding coarse threshold")
    ap.add_argument("--output",       default="table", choices=["table","mermaid","dot","json"])
    args = ap.parse_args()

    events = FIRE_EVENTS
    if args.events_file:
        with open(args.events_file) as f:
            events = json.load(f)

    run(events, args.threshold, args.output)
