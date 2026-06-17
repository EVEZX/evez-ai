#!/usr/bin/env python3
"""Play Engine: generates narrated projections from spine-grade events.

Design goals:
- Offline-friendly: does not require network.
- Append-only: every step is an EVENT_SPINE event with trace_id.
- Projection is mutable: docs/PLAYTHROUGH_LATEST.md can be overwritten, but references immutable trace_ids.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"

MOTIFS = [
    {"lobby":"DNS", "motif":"naming fork", "probe":"compare resolvers + TTL", "falsifier":"authoritative answer matches across resolvers"},
    {"lobby":"BGP", "motif":"route ghost", "probe":"multi-vantage traceroute", "falsifier":"same AS-path + reachability from all vantages"},
    {"lobby":"TLS", "motif":"identity court", "probe":"validate chain + OCSP + time", "falsifier":"chain ok and time stable"},
    {"lobby":"CDN", "motif":"echo hall", "probe":"inspect cache headers + bypass key", "falsifier":"origin and edge agree on freshness"},
    {"lobby":"AUTH", "motif":"clock skew gate", "probe":"compare token iat/exp vs server time", "falsifier":"no skew; token valid everywhere"},
    {"lobby":"ROLLBACK", "motif":"retrocausal correction", "probe":"pending vs final diff by trace_id", "falsifier":"no divergence between client and authoritative"},
    {"lobby":"MIXED", "motif":"symptom impersonation", "probe":"separate layers with discriminating tests", "falsifier":"layer attribution stable across tests"},
    {"lobby":"QUANTUM", "motif":"metaphor abuse", "probe":"require measurement context + error budget", "falsifier":"claim survives explicit context constraints"},
    {"lobby":"FUNDING", "motif":"USD checkpoint", "probe":"require FX snapshot asset + provenance", "falsifier":"no snapshot; claim rejected"},
    {"lobby":"FSC", "motif":"confidence outruns falsifier", "probe":"compress narrative; demand falsifier", "falsifier":"falsifier provided; claim demoted/updated"},
]

def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat() + "Z"

def _append(obj: dict) -> None:
    SPINE.parent.mkdir(parents=True, exist_ok=True)
    if not SPINE.exists():
        SPINE.write_text("# Append-only event spine\n", encoding="utf-8")
    with SPINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _trace_id_from_obj(obj: dict) -> str:
    """Content-addressed trace id (hash of stable JSON)."""
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha256(payload).hexdigest()[:16]
    return f"T{h}"


def _lobby_for_probe_kind(probe_kind: str) -> str:
    return {
        "probe.dns": "DNS",
        "probe.http": "CDN",
        "probe.tls": "TLS",
        "probe.ping": "BGP",
    }.get(probe_kind, "MIXED")


def run_episode(seed: int, steps: int, narrative_style: str = "hud", mission: dict | None = None) -> dict:
    rnd = random.Random(seed)
    ep_id = f"EP-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')}-{seed}"

    triggered_by = None
    if mission and mission.get("trace_id"):
        triggered_by = str(mission.get("trace_id"))

    _append({
        "kind":"play.episode_start",
        "episode_id": ep_id,
        "timestamp": utc_now(),
        "seed": seed,
        "steps": steps,
        "truth_plane":"truth",
        "triggered_by": triggered_by,
        "notes":"Episode start (projection can change; spine cannot)."
    })
    step_rows = []

    # If triggered by a disagreement mission, inject it as step 1 so Σf/Ω are grounded.
    start_step = 1
    if mission:
        ts = utc_now()
        probe_kind = ((mission.get("key") or {}).get("probe_kind") or "")
        lobby = _lobby_for_probe_kind(probe_kind)
        target = ((mission.get("key") or {}).get("target") or {})
        obs = mission.get("observations") or []
        payload = {
            "episode_id": ep_id,
            "step": 1,
            "lobby": lobby,
            "mission_trace": mission.get("trace_id"),
            "probe_kind": probe_kind,
            "target": target,
            "observations": obs,
        }
        trace = _trace_id_from_obj(payload)
        evt = {
            "kind": "play.step",
            "episode_id": ep_id,
            "step": 1,
            "trace_id": trace,
            "timestamp": ts,
            "lobby": lobby,
            "motif": "multi-vantage disagreement",
            "claim": f"Disagreement across vantages for {probe_kind} target={target}.",
            "truth_plane": "pending",
            "proposed_probe": mission.get("recommended_probe"),
            "falsifier": "values converge across vantages on re-probe; divergence explained by named layer",
            "Sigma_f": mission.get("Sigma_f") or [],
            "Omega": mission.get("Omega") or "",
            "source_mission": mission.get("trace_id"),
            "evidence": {"observations": obs},
        }
        _append(evt)
        step_rows.append(evt)
        start_step = 2

    for i in range(start_step, steps + 1):
        ts = utc_now()
        motif = rnd.choice(MOTIFS)
        payload = {
            "episode_id": ep_id,
            "step": i,
            "lobby": motif["lobby"],
            "motif": motif["motif"],
            "seed": seed,
        }
        trace = _trace_id_from_obj(payload)
        # Step event is PENDING by default; it must be proven by probes to become truth.
        evt = {
            "kind":"play.step",
            "episode_id": ep_id,
            "step": i,
            "trace_id": trace,
            "timestamp": ts,
            "lobby": motif["lobby"],
            "motif": motif["motif"],
            "claim": f"In {motif['lobby']}, a failure may present as: {motif['motif']}.",
            "truth_plane":"pending",
            "proposed_probe": motif["probe"],
            "falsifier": motif["falsifier"],
            "Sigma_f": [],
            "Omega": "",
        }
        _append(evt)
        step_rows.append(evt)
    _append({
        "kind":"play.episode_end",
        "episode_id": ep_id,
        "timestamp": utc_now(),
        "truth_plane":"truth",
        "notes":"Episode end."
    })
    return {"episode_id": ep_id, "steps": step_rows}

def render_markdown(episode: dict) -> str:
    ep_id = episode["episode_id"]
    lines = []
    lines.append(f"# PLAYTHROUGH (projection) — {ep_id}")
    lines.append("")
    lines.append("This file is a **mutable projection**. The spine events are immutable. Each step cites a `trace_id` you can grep in `spine/EVENT_SPINE.jsonl`.")
    lines.append("")
    for s in episode["steps"]:
        lines.append(f"## Step {s['step']} — {s['lobby']} / {s['motif']}")
        lines.append(f"- trace_id: `{s['trace_id']}`")
        lines.append(f"- truth_plane: `{s['truth_plane']}`")
        lines.append(f"- claim: {s['claim']}")
        lines.append(f"- falsifier: {s['falsifier']}")
        lines.append(f"- proposed_probe: {s['proposed_probe']}")
        lines.append("")
    lines.append("""---\n\n### HUD tail (what the prompter should watch)\n- If your confidence rises, your falsifier must rise too.\n- If a claim can’t be broken on purpose, it’s theater.\n- The map begins when the mapper is mapped.""")
    lines.append("")
    return "\n".join(lines)

def write_playthrough(md_path: Path, episode: dict) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(episode), encoding="utf-8")
