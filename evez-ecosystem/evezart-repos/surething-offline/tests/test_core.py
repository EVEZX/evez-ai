"""
SureThing Offline — Test Suite
"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("SPINE_PATH","/tmp/test_spine.jsonl")
os.environ.setdefault("TASKS_DB_PATH","/tmp/test_tasks.db")
os.environ.setdefault("DRAFTS_PATH","/tmp/test_drafts")
os.environ.setdefault("CHROMA_PERSIST_DIR","/tmp/test_chroma")
import json,pytest
from fastapi.testclient import TestClient

def test_spine_emit_and_verify():
    import pathlib
    p=pathlib.Path("/tmp/test_spine.jsonl")
    if p.exists(): p.unlink()
    from spine.ledger import emit,verify_chain,read_events
    emit("observation",{"data":"hello"},tags=["test"])
    emit("claim",{"claim":"world"})
    assert len(read_events(limit=10))>=2
    r=verify_chain(); assert r["chain_valid"],f"Chain broken: {r['issues']}"

def test_spine_hash_determinism():
    from spine.ledger import _jcs,_sha256
    obj={"z":1,"a":2,"m":[3,4]}
    assert _sha256(_jcs(obj))==_sha256(_jcs(obj))

def test_task_create_and_get():
    import pathlib; pathlib.Path("/tmp/test_tasks.db").unlink(missing_ok=True)
    from tasks.store import create,get,update,list_tasks
    t=create(title="Test",executor="ai")
    assert t["status"]=="pending"
    assert get(t["id"])["id"]==t["id"]
    assert update(t["id"],status="completed")["status"]=="completed"
    assert any(x["id"]==t["id"] for x in list_tasks(status="completed"))

def test_draft_create_approve():
    import pathlib; pathlib.Path("/tmp/test_drafts").mkdir(exist_ok=True)
    from drafts.store import create,approve,cancel,list_drafts
    d=create("email_draft",{"to":["test@example.com"],"subject":"Hi","body":"Hello"})
    assert d["status"]=="pending"
    assert approve(d["id"])["status"]=="approved"
    d2=create("social_draft",{"platform":"twitter","message":"test"})
    assert cancel(d2["id"])["status"]=="cancelled"

def test_api_health():
    from api.app import app; c=TestClient(app)
    r=c.get("/health"); assert r.status_code==200; assert r.json()["mode"]=="offline"

def test_api_tasks():
    from api.app import app; c=TestClient(app)
    r=c.post("/tasks",json={"title":"Test","executor":"ai"}); assert r.status_code==200
    tid=r.json()["id"]
    assert c.get(f"/tasks/{tid}").status_code==200
    assert c.patch(f"/tasks/{tid}",json={"status":"completed"}).status_code==200

def test_api_spine():
    from api.app import app; c=TestClient(app)
    assert "events" in c.get("/spine").json()
    assert "chain_valid" in c.get("/spine/verify").json()

def test_api_drafts():
    from api.app import app; c=TestClient(app)
    r=c.post("/drafts",json={"type":"email_draft","content":{"to":["x@x.com"],"subject":"T","body":"B"}})
    assert r.status_code==200; did=r.json()["id"]
    assert c.post(f"/drafts/{did}/approve").json()["status"]=="approved"
