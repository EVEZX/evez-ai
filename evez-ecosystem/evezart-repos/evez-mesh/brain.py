#!/usr/bin/env python3
"""
EVEZ Mesh — Decentralized Agent Brain Network
Brain Node: memory + cognition + action + mesh sync

Each brain is an autonomous agent that:
- Stores its own memories (SQLite + vector)
- Thinks via Groq LLM
- Acts via tool execution
- Syncs memories with other brains via gossip protocol
- Identifies unknowns via eigenspectral unfogging
- Serves as a distributed inference node

Built by Steven AI • EVEZ Factory • 2026-05-22
"""

import json, time, hashlib, os, asyncio, logging, sqlite3, struct
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx

# ── Configuration ──────────────────────────────────────

BRAIN_ID = os.getenv("BRAIN_ID", f"brain-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}")
BRAIN_PORT = int(os.getenv("BRAIN_PORT", "8893"))
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
PEERS = [p.strip() for p in os.getenv("MESH_PEERS", "").split(",") if p.strip()]
DB_PATH = os.getenv("BRAIN_DB", f"/home/openclaw/projects/evez-mesh/data/{BRAIN_ID}.db")

app = FastAPI(title=f"EVEZ Mesh Brain {BRAIN_ID}", version="1.0.0")
log = logging.getLogger(f"mesh-{BRAIN_ID}")

# ── Memory Models ──────────────────────────────────────

class Memory(BaseModel):
    id: str = ""
    brain_id: str = BRAIN_ID
    mem_type: str = "semantic"  # semantic, episodic, procedural
    content: str = ""
    embedding: List[float] = Field(default_factory=list)
    confidence: float = 1.0
    timestamp: float = Field(default_factory=time.time)
    vector_clock: int = 0
    tags: List[str] = Field(default_factory=list)

class Thought(BaseModel):
    query: str
    response: str = ""
    brain_id: str = BRAIN_ID
    confidence: float = 0.0
    unfogged: bool = False
    peer_contributions: List[Dict] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)

class BrainStatus(BaseModel):
    brain_id: str
    status: str = "alive"
    memory_count: int = 0
    uptime: float = 0.0
    peers: List[str] = Field(default_factory=list)
    load: float = 0.0
    credits: float = 100.0

# ── Brain Core ─────────────────────────────────────────

class Brain:
    """Single agent brain with local memory, cognition, and mesh sync"""
    
    def __init__(self, brain_id: str = BRAIN_ID):
        self.brain_id = brain_id
        self.peers: List[str] = []
        self.credits = 100.0
        self.vector_clock = 0
        self.start_time = time.time()
        self.memories: Dict[str, Memory] = {}
        self.thoughts: List[Thought] = []
        self._init_db()
    
    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            brain_id TEXT,
            mem_type TEXT,
            content TEXT,
            confidence REAL,
            timestamp REAL,
            vector_clock INTEGER,
            tags TEXT
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(mem_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_brain ON memories(brain_id)")
        self.db.commit()
        # Load existing memories
        for row in self.db.execute("SELECT id, brain_id, mem_type, content, confidence, timestamp, vector_clock, tags FROM memories"):
            mid, bid, mtype, content, conf, ts, vc, tags = row
            self.memories[mid] = Memory(id=mid, brain_id=bid, mem_type=mtype, content=content, confidence=conf, timestamp=ts, vector_clock=vc, tags=json.loads(tags))
        log.info(f"Brain {self.brain_id} loaded {len(self.memories)} memories")
    
    def store(self, memory: Memory) -> Memory:
        if not memory.id:
            memory.id = hashlib.sha256(f"{memory.content}{time.time()}{self.brain_id}".encode()).hexdigest()[:16]
        memory.brain_id = self.brain_id
        self.vector_clock += 1
        memory.vector_clock = self.vector_clock
        
        self.memories[memory.id] = memory
        self.db.execute("INSERT OR REPLACE INTO memories VALUES (?,?,?,?,?,?,?,?)",
            (memory.id, memory.brain_id, memory.mem_type, memory.content, memory.confidence, memory.timestamp, memory.vector_clock, json.dumps(memory.tags)))
        self.db.commit()
        return memory
    
    def recall(self, query: str, limit: int = 5) -> List[Memory]:
        """Simple keyword recall (vector search would replace this)"""
        query_lower = query.lower()
        scored = []
        for m in self.memories.values():
            score = sum(1 for word in query_lower.split() if word in m.content.lower())
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored[:limit]]
    
    def unfog(self, query: str) -> Tuple[bool, List[Memory]]:
        """Identify knowledge gaps for a query — the UNFOGGER
        
        Returns (is_foggy, relevant_memories)
        is_foggy = True means the mesh doesn't know the answer
        """
        relevant = self.recall(query)
        if not relevant:
            return True, []  # Complete fog — no relevant memories
        
        # Check confidence gap
        avg_confidence = sum(m.confidence for m in relevant) / len(relevant)
        if avg_confidence < 0.5:
            return True, relevant  # Low confidence — foggy
        
        return False, relevant  # Clear enough
    
    async def think(self, query: str) -> Thought:
        """Cognition: query → LLM → thought, with mesh unfogging"""
        thought = Thought(query=query)
        
        # 1. Check local memory
        is_foggy, relevant = self.unfog(query)
        
        # 2. If foggy, ask the mesh
        if is_foggy and self.peers:
            peer_answers = await self._ask_mesh(query)
            thought.peer_contributions = peer_answers
            if peer_answers:
                thought.unfogged = True
                # Merge peer answers into context
                peer_context = "\n".join(f"Peer {p['brain_id']}: {p['response']}" for p in peer_answers)
                relevant_content = peer_context
            else:
                relevant_content = "No peer contributions."
        else:
            relevant_content = "\n".join(m.content for m in relevant[:3])
        
        # 3. LLM cognition
        if GROQ_KEY:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    messages = [
                        {"role": "system", "content": f"You are brain {self.brain_id} in the EVEZ Mesh. You think autonomously. Relevant context:\n{relevant_content}"},
                        {"role": "user", "content": query}
                    ]
                    r = await client.post(GROQ_URL, headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}, json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 500})
                    if r.status_code == 200:
                        data = r.json()
                        thought.response = data["choices"][0]["message"]["content"].encode('ascii', 'replace').decode()
                        thought.confidence = 0.9 if not is_foggy else 0.6
                    else:
                        thought.response = f"LLM error: {r.status_code}"
                        thought.confidence = 0.1
            except Exception as e:
                thought.response = f"LLM failed: {e}"
                thought.confidence = 0.1
        else:
            thought.response = f"No LLM key. Local recall: {relevant_content[:200]}"
            thought.confidence = 0.3
        
        self.thoughts.append(thought)
        # Store the thought as episodic memory
        self.store(Memory(mem_type="episodic", content=f"Q: {query} A: {thought.response}", confidence=thought.confidence, tags=["thought", "mesh"]))
        
        return thought
    
    async def _ask_mesh(self, query: str) -> List[Dict]:
        """Ask peer brains for answers — distributed cognition"""
        answers = []
        async with httpx.AsyncClient(timeout=10) as client:
            for peer in self.peers:
                try:
                    r = await client.post(f"http://{peer}/think", json={"query": query}, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        answers.append({"brain_id": data.get("brain_id", peer), "response": data.get("response", ""), "confidence": data.get("confidence", 0)})
                        # Credit the peer
                        self.credits -= 1.0  # Cost of asking
                except:
                    pass  # Peer unreachable — mesh is fault-tolerant
        return answers
    
    def gossip(self) -> List[Memory]:
        """Return recent memories for mesh sync (gossip protocol)"""
        cutoff = time.time() - 300  # Last 5 minutes
        return [m for m in self.memories.values() if m.timestamp > cutoff]
    
    def receive_gossip(self, memories: List[Memory]) -> int:
        """Merge incoming gossip — CRDT-style conflict resolution (last-write-wins by vector clock)"""
        merged = 0
        for m in memories:
            existing = self.memories.get(m.id)
            if not existing or m.vector_clock > existing.vector_clock:
                self.memories[m.id] = m
                self.db.execute("INSERT OR REPLACE INTO memories VALUES (?,?,?,?,?,?,?,?)",
                    (m.id, m.brain_id, m.mem_type, m.content, m.confidence, m.timestamp, m.vector_clock, json.dumps(m.tags)))
                merged += 1
        self.db.commit()
        return merged
    
    def status(self) -> BrainStatus:
        return BrainStatus(
            brain_id=self.brain_id,
            memory_count=len(self.memories),
            uptime=round(time.time() - self.start_time, 1),
            peers=self.peers,
            load=len(self.thoughts) / max(1, self.uptime / 60),
            credits=self.credits
        )

brain = Brain()

# ── API Endpoints ──────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "alive", "brain_id": brain.brain_id, "memories": len(brain.memories)}

@app.get("/status")
def get_status():
    return brain.status().dict()

@app.post("/memorize")
def memorize(memory: Memory):
    m = brain.store(memory)
    return {"id": m.id, "brain_id": m.brain_id, "vector_clock": m.vector_clock}

@app.post("/recall")
def recall(query: str, limit: int = 5):
    results = brain.recall(query, limit)
    return {"query": query, "results": [m.dict() for m in results], "count": len(results)}

@app.post("/think")
async def think(query: str):
    thought = await brain.think(query)
    return thought.dict()

@app.get("/unfog")
def unfog(query: str):
    is_foggy, relevant = brain.unfog(query)
    return {"query": query, "foggy": is_foggy, "relevant_memories": [m.dict() for m in relevant], "fog_level": "complete" if is_foggy and not relevant else "partial" if is_foggy else "clear"}

@app.get("/gossip")
def get_gossip():
    """Return recent memories for mesh sync"""
    mems = brain.gossip()
    return {"brain_id": brain.brain_id, "memories": [m.dict() for m in mems], "count": len(mems)}

@app.post("/gossip")
def receive_gossip(memories: List[Memory]):
    """Receive gossip from a peer"""
    merged = brain.receive_gossip(memories)
    return {"merged": merged, "total_memories": len(brain.memories)}

@app.post("/peers")
def add_peer(url: str):
    brain.peers.append(url)
    return {"brain_id": brain.brain_id, "peers": brain.peers}

@app.get("/peers")
def list_peers():
    return {"brain_id": brain.brain_id, "peers": brain.peers}

@app.get("/credits")
def get_credits():
    return {"brain_id": brain.brain_id, "credits": brain.credits}

@app.get("/eigenspectrum")
def eigenspectrum():
    """Compute eigenspectrum of the brain's memory graph — the unfogger's core"""
    # Build adjacency from memory tags
    import numpy as np
    n = len(brain.memories)
    if n < 2:
        return {"error": "Need 2+ memories for eigenspectrum", "fog_index": 1.0}
    
    mems = list(brain.memories.values())
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            overlap = len(set(mems[i].tags) & set(mems[j].tags))
            if overlap > 0:
                A[i][j] = overlap
                A[j][i] = overlap
    
    eigenvalues = sorted(np.linalg.eigvalsh(A), reverse=True)
    neg_eigs = [e for e in eigenvalues if e < -0.001]
    pos_eigs = [e for e in eigenvalues if e > 0.001]
    
    fog_index = len(neg_eigs) / max(1, n)  # More negative eigenvalues = more fog
    dominant_gap = abs(min(eigenvalues)) if eigenvalues else 0
    
    return {
        "brain_id": brain.brain_id,
        "memory_count": n,
        "eigenvalues": [round(e, 4) for e in eigenvalues[:10]],
        "positive_count": len(pos_eigs),
        "negative_count": len(neg_eigs),
        "dominant_gap": round(dominant_gap, 4),
        "fog_index": round(fog_index, 4),  # 0 = clear, 1 = total fog
        "mesh_coherence": round(sum(pos_eigs) / (sum(pos_eigs) + dominant_gap), 4) if sum(pos_eigs) > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=BRAIN_PORT)
