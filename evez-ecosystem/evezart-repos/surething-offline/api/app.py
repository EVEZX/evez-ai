"""
SureThing Offline — FastAPI Application
"""
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="SureThing Offline", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class _WS:
    def __init__(self): self.active=[]
    async def connect(self,ws): await ws.accept(); self.active.append(ws)
    def disconnect(self,ws): self.active=[c for c in self.active if c!=ws]
    async def broadcast(self,msg):
        for ws in list(self.active):
            try: await ws.send_json(msg)
            except: self.disconnect(ws)
mgr = _WS()

class ChatMsg(BaseModel): message:str; conversation_id:Optional[str]=None
class TaskCreate(BaseModel): title:str; executor:str="ai"; action:Optional[str]=None; why_human:Optional[str]=None
class DraftCreate(BaseModel): type:str; content:dict
class MemSave(BaseModel): content:str; category:str="general"

@app.get("/health")
async def health():
    from brain.llm import health as lh; from memory.store import health as mh
    from spine.ledger import verify_chain; from monitors.email_monitor import IMAP_ENABLED
    return {"status":"online","mode":"offline","llm":lh(),"memory":mh(),"spine":verify_chain(),"email_monitor":{"enabled":IMAP_ENABLED}}

@app.post("/chat")
async def chat(body:ChatMsg):
    from brain.llm import chat as lc; from memory.store import search; from spine.ledger import emit
    mr = search(body.message, n_results=3)
    mc = "\n".join(f"[{r['metadata'].get('category','?')}] {r['content']}" for r in mr) if mr else None
    response = lc([{"role":"user","content":body.message}], memory_context=mc)
    emit("transformation",{"user_message":body.message[:500],"response_preview":response[:200]},
         operator_lane="system",subject="chat",tags=["chat"])
    await mgr.broadcast({"type":"chat_response","message":response,"conversation_id":body.conversation_id})
    return {"response":response,"conversation_id":body.conversation_id}

@app.websocket("/ws")
async def ws(websocket:WebSocket):
    await mgr.connect(websocket)
    try:
        while True:
            data=await websocket.receive_json()
            if data.get("type")=="chat":
                from brain.llm import chat as lc
                await websocket.send_json({"type":"response","content":lc([{"role":"user","content":data["message"]}])})
    except WebSocketDisconnect: mgr.disconnect(websocket)

@app.get("/tasks"); async def list_tasks(status:Optional[str]=None,executor:Optional[str]=None):
    from tasks.store import list_tasks as lt; return {"tasks":lt(status=status,executor=executor)}
@app.post("/tasks"); async def create_task(body:TaskCreate):
    from tasks.store import create; return create(title=body.title,executor=body.executor,action=body.action,why_human=body.why_human)
@app.get("/tasks/{task_id}"); async def get_task(task_id:str):
    from tasks.store import get; t=get(task_id);
    if not t: raise HTTPException(404,"Not found"); return t
@app.patch("/tasks/{task_id}"); async def update_task(task_id:str,body:dict):
    from tasks.store import update; return update(task_id,**body)
@app.delete("/tasks/{task_id}"); async def del_task(task_id:str):
    from tasks.store import delete; return {"deleted":delete(task_id)}

@app.get("/drafts"); async def list_drafts(status:Optional[str]=None):
    from drafts.store import list_drafts as ld; return {"drafts":ld(status=status)}
@app.post("/drafts"); async def create_draft(body:DraftCreate):
    from drafts.store import create; return create(draft_type=body.type,content=body.content)
@app.get("/drafts/{draft_id}"); async def get_draft(draft_id:str):
    from drafts.store import get; d=get(draft_id);
    if not d: raise HTTPException(404,"Not found"); return d
@app.post("/drafts/{draft_id}/approve"); async def approve_draft(draft_id:str):
    from drafts.store import approve; d=approve(draft_id);
    if not d: raise HTTPException(404,"Not found"); return d
@app.post("/drafts/{draft_id}/cancel"); async def cancel_draft(draft_id:str):
    from drafts.store import cancel; d=cancel(draft_id);
    if not d: raise HTTPException(404,"Not found"); return d

@app.get("/spine"); async def get_spine(limit:int=50,offset:int=0):
    from spine.ledger import read_events; return {"events":read_events(limit=limit,offset=offset)}
@app.get("/spine/verify"); async def verify_spine():
    from spine.ledger import verify_chain; return verify_chain()

@app.get("/memory"); async def search_memory(q:str,category:Optional[str]=None,n:int=5):
    from memory.store import search; return {"results":search(q,category=category,n_results=n)}
@app.post("/memory"); async def save_memory(body:MemSave):
    from memory.store import save; return {"id":save(body.content,category=body.category),"saved":True}
@app.delete("/memory/{mem_id}"); async def del_memory(mem_id:str):
    from memory.store import delete; return {"deleted":delete(mem_id)}

@app.post("/email/poll"); async def poll_email():
    from monitors.email_monitor import poll_once; emails=poll_once(); return {"fetched":len(emails),"emails":emails}

FALLBACK_UI = '''<!DOCTYPE html>
<html><head><title>SureThing Offline</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#e8e8e8;height:100vh;display:flex;flex-direction:column}header{padding:16px 24px;background:#111;border-bottom:1px solid #222;display:flex;align-items:center;gap:12px}.logo{font-weight:700;font-size:18px;letter-spacing:-.5px}.badge{background:#1a3a2a;color:#4ade80;font-size:11px;padding:2px 8px;border-radius:99px;font-weight:600}.status{margin-left:auto;font-size:12px;color:#666}.status.online{color:#4ade80}main{flex:1;display:flex;overflow:hidden}#messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:16px}.msg{max-width:680px;padding:12px 16px;border-radius:12px;line-height:1.5;font-size:14px}.msg.user{background:#1e3a5f;align-self:flex-end}.msg.assistant{background:#1a1a1a;border:1px solid #2a2a2a;align-self:flex-start}.msg.system{background:#1a2a1a;border:1px solid #2a3a2a;align-self:center;font-size:12px;color:#4ade80}footer{padding:16px 24px;background:#111;border-top:1px solid #222}.input-row{display:flex;gap:12px}#input{flex:1;background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:12px 16px;color:#e8e8e8;font-size:14px;outline:none}#input:focus{border-color:#4ade80}#send{background:#166534;color:#4ade80;border:none;border-radius:10px;padding:12px 20px;font-size:14px;font-weight:600;cursor:pointer}#send:hover{background:#15803d}.thinking{color:#666;font-style:italic;font-size:13px}</style>
</head><body>
<header><div class="logo">SureThing</div><div class="badge">OFFLINE</div><div class="status" id="status">checking...</div></header>
<main><div id="messages"><div class="msg system">Running offline. No cloud. No paywall. Full control.</div></div></main>
<footer><div class="input-row"><input id="input" placeholder="Message SureThing..." autocomplete="off"/><button id="send">Send</button></div></footer>
<script>
const messages=document.getElementById("messages"),input=document.getElementById("input"),send=document.getElementById("send"),status=document.getElementById("status");
async function checkHealth(){try{const r=await fetch("/health"),d=await r.json(),m=d.llm?.model||"unknown",l=d.llm?.model_loaded;status.textContent=l?`\u25cf ${m}`:`\u25cb ${m} (not loaded)`;status.className="status "+(l?"online":"")}catch{status.textContent="\u25cb server offline"}}
function addMsg(role,content){const el=document.createElement("div");el.className="msg "+role;el.textContent=content;messages.appendChild(el);messages.scrollTop=messages.scrollHeight;return el}
async function sendMessage(){const text=input.value.trim();if(!text)return;input.value="";addMsg("user",text);const t=addMsg("assistant","...");t.classList.add("thinking");try{const r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})}),d=await r.json();t.textContent=d.response;t.classList.remove("thinking")}catch{t.textContent="[Error reaching server]";t.classList.remove("thinking")}}
send.addEventListener("click",sendMessage);input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendMessage()}});checkHealth();setInterval(checkHealth,30000);
</script></body></html>'''

@app.get("/", response_class=HTMLResponse)
async def root(): return HTMLResponse(FALLBACK_UI)
