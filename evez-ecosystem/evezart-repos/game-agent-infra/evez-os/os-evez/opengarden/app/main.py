"""opengarden.app.main — FastAPI server."""
import os, json, time, hashlib, shutil, zipfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

DATA_DIR = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
CREATOR = os.environ.get("OG_CREATOR_NAME", "Steven Crawford-Maggard")
HANDLE  = os.environ.get("OG_CREATOR_HANDLE", "EVEZ666")
REPO    = os.environ.get("OG_CREATOR_REPO", "github.com/EvezArt/evez-os")
LICENSE = os.environ.get("OG_LICENSE_ID", "AGPL-3.0")
FREE_LAG = int(os.environ.get("OG_FREE_LAG_RUNS", "5"))
DL_TOKEN = os.environ.get("OG_DOWNLOAD_TOKEN", "")

app = FastAPI(title="OS-EVEZ OpenGarden", version="1.0.0")

def runs_dir():    return DATA_DIR / "runs"
def fixtures_dir(): return DATA_DIR / "fixtures"
def ledger_spine():
    from evezos.spine import Spine
    return Spine(DATA_DIR / "ledger" / "spine.jsonl")

def list_runs() -> list[str]:
    d = runs_dir()
    if not d.exists(): return []
    return sorted([r.name for r in d.iterdir() if r.is_dir()], reverse=True)

def check_token(request: Request):
    if not DL_TOKEN: return True
    token = request.query_params.get("token") or request.headers.get("X-OG-Token", "")
    return token == DL_TOKEN


@app.get("/health")
def health():
    return {"ok": True, "creator": CREATOR, "handle": HANDLE, "repo": REPO, "ts": time.time()}


@app.get("/arcade", response_class=HTMLResponse)
def arcade():
    runs = list_runs()
    items = "".join(f"<li><a href='/runs/{r}'>{r}</a></li>" for r in runs[:20])
    return f"""<!DOCTYPE html><html><head><title>OS-EVEZ ARCADE</title>
<style>body{{font-family:monospace;background:#111;color:#0f0;padding:24px}}</style></head>
<body><h1>◊ OS-EVEZ ARCADE</h1>
<p>Creator: {CREATOR} ({HANDLE}) | {REPO}</p>
<p>Runs: {len(runs)}</p><ul>{items or "<li>No runs yet. POST /runs/create to begin.</li>"}</ul>
<p><a href="/market">→ Market</a> | <a href="/public-key.html">→ Public Key</a> | <a href="/assets/map.html">→ Assets</a></p>
</body></html>"""


@app.get("/events")
def events():
    from evezos.spine import Spine
    s = Spine(DATA_DIR / "events_spine.jsonl")
    return {"events": s.read_all()[-50:]}


@app.get("/market", response_class=HTMLResponse)
def market():
    runs = list_runs()
    latest = runs[0] if runs else "none"
    return f"""<!DOCTYPE html><html><head><title>OS-EVEZ Market</title>
<style>body{{font-family:monospace;background:#111;color:#ff0;padding:24px}}</style></head>
<body><h1>◊ OS-EVEZ Market</h1>
<p>Creator: {CREATOR} | License: {LICENSE}</p>
<p>Latest run: {latest}</p>
<p><a href="/latest/download{("?token="+DL_TOKEN) if DL_TOKEN else ""}">⬇ Download Latest Bundle</a></p>
<p><a href="/free/download">⬇ Free Sample (lagged {FREE_LAG} runs)</a></p>
<p>github.com/EvezArt/evez-os</p>
</body></html>"""


@app.post("/runs/create")
async def create_run(request: Request):
    import random
    body = {}
    try: body = await request.json()
    except: pass
    seed = body.get("seed", random.randint(0, 9999))
    steps = body.get("steps", 35)
    set_default = body.get("set_default", False)

    run_id = f"run_{int(time.time())}_{seed}"
    run_dir = runs_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    from evezos.spine import Spine
    from evezos.manifest import build_manifest
    spine = Spine(run_dir / "spine.jsonl")

    for i in range(steps):
        spine.append("step", {"step": i, "seed": seed, "val": round((seed * (i+1)) % 1000 / 1000, 6)})

    events = spine.read_all()
    mf = build_manifest(run_id, run_dir, events)

    # Write index.html
    (run_dir / "index.html").write_text(f"""<!DOCTYPE html><html><head><title>{run_id}</title></head>
<body><h1>{run_id}</h1><p>Steps: {steps} | Seed: {seed}</p>
<p>Root hash: {mf["root_hash"][:32]}...</p>
<p>Creator: {CREATOR} ({HANDLE})</p></body></html>""")

    # Write arcade.html
    (run_dir / "artifacts").mkdir(exist_ok=True)
    (run_dir / "artifacts" / "arcade.html").write_text(f"""<!DOCTYPE html><html><head><title>Arcade: {run_id}</title></head>
<body><h1>◊ {run_id}</h1><p>{steps} spine events. Root: {mf["root_hash"][:20]}...</p></body></html>""")

    # Provenance
    (run_dir / "provenance").mkdir(exist_ok=True)
    attribution = f"# ATTRIBUTION\nCreator: {CREATOR}\nHandle: {HANDLE}\nRepo: {REPO}\nLicense: {LICENSE}\nRun: {run_id}\n"
    (run_dir / "provenance" / "ATTRIBUTION.md").write_text(attribution)

    prov_mf = {"run_id": run_id, "creator": CREATOR, "handle": HANDLE, "root_hash": mf["root_hash"], "spine_events": len(events)}

    # Sign
    sig = _sign(json.dumps(prov_mf, sort_keys=True))
    prov_mf["signature"] = sig
    (run_dir / "provenance" / "bundle_manifest.json").write_text(json.dumps(prov_mf, indent=2))
    (run_dir / "manifest.json").write_text(json.dumps(mf, indent=2))

    # ZIP bundle
    bundle_path = run_dir / "run_bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in run_dir.rglob("*"):
            if f.is_file() and f.name != "run_bundle.zip":
                zf.write(f, f.relative_to(run_dir))

    ledger_spine().append("run_created", {"run_id": run_id, "steps": steps, "seed": seed, "root_hash": mf["root_hash"]})

    if set_default:
        (DATA_DIR / "default_run.txt").write_text(run_id)

    return {"run_id": run_id, "steps": steps, "root_hash": mf["root_hash"], "bundle": str(bundle_path)}


def _sign(data: str) -> str:
    key_file = DATA_DIR / "keys" / "signing_key.json"
    if not key_file.exists():
        return "unsigned"
    key = json.loads(key_file.read_text())
    if "secret" in key:
        import hmac, hashlib
        return hmac.new(key["secret"].encode(), data.encode(), hashlib.sha256).hexdigest()
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        priv_bytes = bytes.fromhex(key["private"])
        priv = Ed25519PrivateKey.from_private_bytes(priv_bytes)
        sig = priv.sign(data.encode())
        return sig.hex()
    except Exception:
        return "sign_error"


@app.get("/latest")
def latest():
    runs = list_runs()
    if not runs: raise HTTPException(404, "no runs")
    run_id = runs[0]
    mf_path = runs_dir() / run_id / "manifest.json"
    mf = json.loads(mf_path.read_text()) if mf_path.exists() else {}
    return {"run_id": run_id, "root_hash": mf.get("root_hash", ""), "bundle": f"/runs/{run_id}/download"}


@app.get("/latest/download")
def latest_download(request: Request):
    if not check_token(request): raise HTTPException(403, "token required")
    runs = list_runs()
    if not runs: raise HTTPException(404, "no runs")
    bundle = runs_dir() / runs[0] / "run_bundle.zip"
    if not bundle.exists(): raise HTTPException(404, "bundle not found")
    ledger_spine().append("download", {"run_id": runs[0], "type": "latest"})
    return FileResponse(bundle, media_type="application/zip", filename=f"{runs[0]}.zip")


@app.get("/free/download")
def free_download():
    runs = list_runs()
    if len(runs) <= FREE_LAG: raise HTTPException(404, "no free run available yet")
    run_id = runs[FREE_LAG]
    bundle = runs_dir() / run_id / "run_bundle.zip"
    if not bundle.exists(): raise HTTPException(404, "bundle not found")
    ledger_spine().append("download", {"run_id": run_id, "type": "free"})
    return FileResponse(bundle, media_type="application/zip", filename=f"{run_id}_free.zip")


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    run_dir = runs_dir() / run_id
    if not run_dir.exists(): raise HTTPException(404, "run not found")
    mf_path = run_dir / "manifest.json"
    mf = json.loads(mf_path.read_text()) if mf_path.exists() else {}
    return {"run_id": run_id, "root_hash": mf.get("root_hash", ""), "files": list(mf.get("files", {}).keys())}


@app.get("/runs/{run_id}/download")
def download_run(run_id: str, request: Request):
    if not check_token(request): raise HTTPException(403, "token required")
    bundle = runs_dir() / run_id / "run_bundle.zip"
    if not bundle.exists(): raise HTTPException(404, "bundle not found")
    ledger_spine().append("download", {"run_id": run_id, "type": "direct"})
    return FileResponse(bundle, media_type="application/zip", filename=f"{run_id}.zip")


@app.post("/fixtures/upload")
async def upload_fixture(file: UploadFile = File(...), name: str = Query("")):
    fixtures_dir().mkdir(parents=True, exist_ok=True)
    out = fixtures_dir() / (name or file.filename)
    out.write_bytes(await file.read())
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    ledger_spine().append("fixture_upload", {"name": name, "sha256": sha, "size": out.stat().st_size})
    return {"name": name, "sha256": sha, "size": out.stat().st_size}


@app.get("/public-key")
def public_key():
    key_file = DATA_DIR / "keys" / "signing_key.json"
    if not key_file.exists(): raise HTTPException(404, "key not generated yet — run bootstrap")
    key = json.loads(key_file.read_text())
    return {"creator": CREATOR, "handle": HANDLE, "public_key": key.get("public", "mac_mode"), "repo": REPO}


@app.get("/public-key.html", response_class=HTMLResponse)
def public_key_html():
    key_file = DATA_DIR / "keys" / "signing_key.json"
    pub = "not yet generated"
    if key_file.exists():
        k = json.loads(key_file.read_text())
        pub = k.get("public", "mac_mode")
    return f"""<!DOCTYPE html><html><head><title>OS-EVEZ Public Key</title>
<style>body{{font-family:monospace;background:#111;color:#0ff;padding:24px}}pre{{background:#222;padding:12px;border-radius:8px}}</style></head>
<body><h1>◊ OS-EVEZ Public Key</h1>
<p>Creator: {CREATOR} | {HANDLE} | {REPO}</p>
<pre>{pub}</pre>
<p>Verify any run_bundle.zip provenance/bundle_manifest.json against this key.</p>
</body></html>"""


@app.get("/maps/latest")
def maps_latest():
    maps_file = DATA_DIR / "maps" / "latest.json"
    if not maps_file.exists(): return {"runs": [], "updated": 0}
    return json.loads(maps_file.read_text())


@app.get("/maps/all")
def maps_all():
    maps_file = DATA_DIR / "maps" / "all.json"
    if not maps_file.exists(): return {"runs": []}
    return json.loads(maps_file.read_text())


@app.get("/assets/scope")
def assets_scope_get():
    scope_file = DATA_DIR / "assets_scope.yaml"
    if not scope_file.exists():
        return {"owners": [CREATOR], "allow": {"filesystem_roots": [str(DATA_DIR)]}, "deny": ["0.0.0.0/0"]}
    import yaml
    return yaml.safe_load(scope_file.read_text())


@app.post("/assets/discover")
def assets_discover():
    runs = list_runs()
    assets = {"updated": time.time(), "creator": CREATOR, "runs": runs[:20], "count": len(runs)}
    sig = _sign(json.dumps(assets, sort_keys=True))
    assets["signature"] = sig
    (DATA_DIR / "assets").mkdir(exist_ok=True)
    (DATA_DIR / "assets" / "map.json").write_text(json.dumps(assets, indent=2))
    return assets


@app.get("/assets/map.html", response_class=HTMLResponse)
def assets_map_html():
    map_file = DATA_DIR / "assets" / "map.json"
    data = json.loads(map_file.read_text()) if map_file.exists() else {}
    runs_html = "".join(f"<li>{r}</li>" for r in data.get("runs", []))
    return f"""<!DOCTYPE html><html><head><title>OS-EVEZ Assets Map</title>
<style>body{{font-family:monospace;background:#111;color:#f80;padding:24px}}</style></head>
<body><h1>◊ OS-EVEZ Assets Map</h1>
<p>Creator: {CREATOR} | Runs: {data.get("count", 0)}</p>
<ul>{runs_html or "<li>No assets yet. POST /assets/discover</li>"}</ul>
<p>Sig: {str(data.get("signature",""))[:32]}...</p>
</body></html>"""


@app.post("/players/register")
async def players_register(request: Request):
    body = await request.json()
    player_id = body.get("player_id", "unknown")
    players_file = DATA_DIR / "players.json"
    players = json.loads(players_file.read_text()) if players_file.exists() else {}
    players[player_id] = {"registered": time.time(), "syncs": 0}
    players_file.write_text(json.dumps(players, indent=2))
    ledger_spine().append("player_register", {"player_id": player_id})
    return {"player_id": player_id, "ok": True}


@app.get("/players/sync/{player_id}")
def players_sync(player_id: str):
    runs = list_runs()
    maps_data = {}
    map_file = DATA_DIR / "assets" / "map.json"
    if map_file.exists():
        maps_data = json.loads(map_file.read_text())
    return {"player_id": player_id, "latest_run": runs[0] if runs else None,
            "top_runs": runs[:5], "maps": maps_data, "ts": time.time()}


@app.post("/schedule")
async def set_schedule(request: Request):
    body = await request.json()
    cfg_path = DATA_DIR / "scheduler_config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(body, indent=2))
    return {"ok": True, "config": body}


@app.post("/schedule/stop")
def schedule_stop():
    stop_file = DATA_DIR / "STOP"
    stop_file.touch()
    return {"ok": True, "msg": "STOP file created — all loops will halt"}


@app.get("/ledger")
def ledger():
    from evezos.spine import Spine
    s = Spine(DATA_DIR / "ledger" / "spine.jsonl")
    return {"events": s.read_all()[-100:]}
