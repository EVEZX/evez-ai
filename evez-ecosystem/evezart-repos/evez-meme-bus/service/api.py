"""
Meme Bus FastAPI control plane v2.1 — with CPF GateLock router mounted.
Endpoints: /healthz /readyz /queue-status /tail /drafts /published /fire-feed /spine /audio
           /cpf/gatelock  /cpf/result  /cpf/vectors  /cpf/validate
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from bus.events import EVENT_LOG_PATH
from cpf.api_routes import router as cpf_router
import json, pathlib, os

app = FastAPI(title="EVEZ Meme Bus + CPF", version="2.1.0")
app.include_router(cpf_router, prefix="/cpf")

SPINE_LOG = pathlib.Path(os.getenv("SPINE_LOG_PATH", "../spine/fire_log.jsonl"))
AUDIO_DIR = pathlib.Path("assets/audio")
OUT_DIR   = pathlib.Path("assets/output_memes")

def _events(kind_filter=None):
    if not EVENT_LOG_PATH.exists():
        return []
    evs = []
    for l in EVENT_LOG_PATH.read_text().splitlines():
        if not l.strip(): continue
        try:
            ev = json.loads(l)
            if kind_filter is None or ev.get("kind") in kind_filter:
                evs.append(ev)
        except Exception:
            pass
    return evs

@app.get("/healthz")
def health(): return {"status": "ok", "version": "2.1.0"}

@app.get("/readyz")
def ready(): return {"status": "ready", "log": str(EVENT_LOG_PATH)}

@app.get("/queue-status")
def queue_status():
    evs = _events()
    counts = {}
    for ev in evs:
        k = ev.get("kind", "?")
        counts[k] = counts.get(k, 0) + 1
    return {"total": len(evs), "by_kind": counts}

@app.get("/tail")
def tail_log(n: int = 20): return {"events": _events()[-n:]}

@app.get("/drafts")
def list_drafts():
    approved = _events(["MEME_APPROVED"])
    posted_ids = {ev.get("payload", {}).get("event_id") for ev in _events(["MEME_POSTED", "MEME_PUBLISHED"])}
    return {"count": len([ev for ev in approved if ev.get("id") not in posted_ids]),
            "drafts": [ev for ev in approved if ev.get("id") not in posted_ids][-20:]}

@app.get("/published")
def list_published():
    posted = _events(["MEME_POSTED", "MEME_PUBLISHED", "MEME_RENDERED"])
    return {"count": len(posted), "published": posted[-30:]}

@app.get("/fire-feed")
def fire_feed():
    fires = _events(["FIRE_EVENT"])
    return {
        "count": len(fires),
        "latest": fires[-10:],
        "last_fire_number": fires[-1]["payload"].get("fire_number") if fires else None,
        "last_v": fires[-1]["payload"].get("v_value") if fires else None,
    }

@app.get("/spine")
def spine_tail(n: int = 10):
    if not SPINE_LOG.exists():
        return {"entries": [], "note": "spine not found at " + str(SPINE_LOG)}
    lines = [l for l in SPINE_LOG.read_text().splitlines() if l.strip()]
    entries = []
    for l in lines[-n:]:
        try: entries.append(json.loads(l))
        except: pass
    return {"count": len(lines), "tail": entries}

@app.get("/audio")
def list_audio():
    if not AUDIO_DIR.exists(): return {"files": []}
    files = sorted(AUDIO_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"count": len(files), "files": [str(f) for f in files[:20]]}

@app.get("/audio/{filename}")
def serve_audio(filename: str):
    path = AUDIO_DIR / filename
    if not path.exists() or path.suffix != ".mp3":
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(str(path), media_type="audio/mpeg")

@app.get("/meme/{filename}")
def serve_meme(filename: str):
    path = OUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(str(path), media_type="image/jpeg")
