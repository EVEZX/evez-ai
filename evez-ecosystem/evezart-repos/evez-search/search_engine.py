#!/usr/bin/env python3
"""
EVEZ Search Engine — Specialized for the EVEZ-OS Ecosystem
Searches across all 18 services, GitHub repos, API endpoints, research papers,
mesh nodes, factory products, and phenomenologic manifold states.
"""
import os, json, time, sqlite3, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
import requests
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("EVZ_SEARCH_BASE", "/home/openclaw/projects/evez-search"))
DB_PATH = BASE / "search.db"
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GITHUB_PAT = os.getenv("GITHUB_PAT", "")

# ─── Service Registry ─────────────────────────────────────────────
EVEZ_SERVICES = {
    "clawbreak": {"port": 8080, "type": "ai-chat", "tags": ["chat", "fsc", "doctrine", "ai"]},
    "cognition": {"port": 8081, "type": "forensics", "tags": ["audit", "forensics", "hallucination"]},
    "factory": {"port": 8891, "type": "manufacturing", "tags": ["code-gen", "autonomous", "github"]},
    "research": {"port": 8892, "type": "research", "tags": ["math", "audit", "paper", "academic"]},
    "breakcore": {"port": 8896, "type": "media", "tags": ["music", "breakcore", "audio", "stream"]},
    "livestream": {"port": 8900, "type": "media", "tags": ["stream", "visualizer", "youtube"]},
    "stream_manager": {"port": 8897, "type": "media", "tags": ["rtmp", "stream", "chat"]},
    "meshmind": {"port": 8899, "type": "infrastructure", "tags": ["mesh", "healing", "thermal"]},
    "mesh_broker": {"port": 8894, "type": "infrastructure", "tags": ["mesh", "broker", "decentralized"]},
    "omega": {"port": 8875, "type": "orchestration", "tags": ["conductor", "workflow", "groq"]},
    "ledger": {"port": 8876, "type": "economics", "tags": ["credits", "auction", "resources"]},
    "bridge": {"port": 8083, "type": "dashboard", "tags": ["dashboard", "intelligence", "events"]},
    "maes": {"port": 8082, "type": "events", "tags": ["spine", "agents", "events"]},
    "pte": {"port": 8901, "type": "phenomenologic", "tags": ["manifold", "topology", "basin", "states"]},
    "rsr": {"port": 8902, "type": "phenomenologic", "tags": ["retrocausal", "stride", "future"]},
    "assembler": {"port": 8903, "type": "phenomenologic", "tags": ["shuffle", "inscribe", "harpoon", "forms"]},
    "commerce": {"port": 8904, "type": "monetization", "tags": ["billing", "stripe", "api-key", "revenue"]},
    "searxng": {"port": 8888, "type": "search", "tags": ["web", "meta-search", "privacy"]},
}

# ─── Search Index ─────────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS search_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, source_type TEXT, title TEXT, content TEXT,
        tags TEXT, url TEXT, metadata TEXT, content_hash TEXT,
        indexed_at TEXT, relevance_score REAL DEFAULT 1.0
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_source ON search_index(source)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON search_index(source_type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tags ON search_index(tags)")
    db.execute("""CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT, results_count INTEGER, latency_ms INTEGER, timestamp TEXT
    )""")
    db.commit()
    return db

DB = init_db()

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def index_item(source, source_type, title, content, tags, url="", metadata=None):
    chash = hash_content(content)
    existing = DB.execute("SELECT id FROM search_index WHERE content_hash = ?", (chash,)).fetchone()
    if existing:
        DB.execute("UPDATE search_index SET indexed_at = ? WHERE id = ?",
                   (datetime.now(timezone.utc).isoformat(), existing[0]))
        return existing[0]
    DB.execute(
        "INSERT INTO search_index (source, source_type, title, content, tags, url, metadata, content_hash, indexed_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (source, source_type, title, content,
         json.dumps(tags) if isinstance(tags, list) else tags, url,
         json.dumps(metadata or {}), chash, datetime.now(timezone.utc).isoformat())
    )
    DB.commit()
    return DB.execute("SELECT last_insert_rowid()").fetchone()[0]

# ─── Crawlers ─────────────────────────────────────────────────────
def crawl_services():
    count = 0
    for name, svc in EVEZ_SERVICES.items():
        try:
            r = requests.get(f"http://localhost:{svc['port']}/", timeout=5)
            if r.ok:
                data = r.json() if "json" in r.headers.get("content-type", "") else {"raw": r.text[:500]}
                index_item(source=name, source_type="service",
                    title=data.get("service", data.get("title", name)),
                    content=json.dumps(data)[:2000], tags=svc["tags"],
                    url=f"http://localhost:{svc['port']}/",
                    metadata={"port": svc["port"], "type": svc["type"]})
                count += 1
                for ep in ["/status", "/stats", "/catalog", "/manifold", "/candidates", "/investor", "/strides"]:
                    try:
                        r2 = requests.get(f"http://localhost:{svc['port']}{ep}", timeout=3)
                        if r2.ok:
                            d2 = r2.json()
                            index_item(source=f"{name}{ep}", source_type="service_endpoint",
                                title=f"{name} {ep}", content=json.dumps(d2)[:2000],
                                tags=svc["tags"] + [ep.strip("/")],
                                url=f"http://localhost:{svc['port']}{ep}")
                            count += 1
                    except:
                        pass
        except:
            pass
    return count

def crawl_github():
    count = 0
    try:
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get("https://api.github.com/orgs/EvezArt/repos?per_page=100&sort=updated",
                        headers=headers, timeout=15)
        if r.ok:
            for repo in r.json():
                topics = repo.get("topics", [])
                desc = repo.get("description", "") or ""
                lang = repo.get("language", "") or ""
                index_item(source=repo["name"], source_type="github_repo",
                    title=repo["full_name"],
                    content=f"{desc} | Language: {lang} | Stars: {repo.get('stargazers_count',0)} | Topics: {', '.join(topics)}",
                    tags=topics + ([lang.lower()] if lang else []),
                    url=repo["html_url"],
                    metadata={"stars": repo.get("stargazers_count",0), "language": lang,
                              "forks": repo.get("forks_count",0), "updated": repo.get("updated_at","")})
                count += 1
    except Exception as e:
        print(f"GitHub crawl error: {e}")
    return count

def crawl_research():
    count = 0
    for path in ["/home/openclaw/projects/evez-research/AUDIT.md",
                 "/home/openclaw/projects/evez-research/PAPER.md"]:
        try:
            with open(path) as f:
                content = f.read()
            index_item(source=Path(path).stem, source_type="research",
                title=f"EVEZ Research: {Path(path).stem}", content=content[:5000],
                tags=["research","math","audit","paper"],
                url="https://github.com/EvezArt/evez-research")
            count += 1
        except:
            pass
    return count

def crawl_manifolds():
    count = 0
    for path in ["/home/openclaw/projects/evez-phenomenologic/circuit/phenomenologic/state.manifold.json",
                 "/home/openclaw/projects/evez-phenomenologic/circuit/phenomenologic/policy.flowfield.json",
                 "/home/openclaw/projects/evez-phenomenologic/circuit/retrocausal/omega_frame.timeline.json"]:
        try:
            with open(path) as f:
                content = f.read()
            data = json.loads(content)
            title = data.get("identity", Path(path).stem)
            index_item(source=Path(path).stem, source_type="manifold",
                title=f"Manifold: {title}", content=content[:3000],
                tags=["phenomenologic","manifold","topology","basin"],
                url="https://github.com/EvezArt/evez-phenomenologic")
            count += 1
        except:
            pass
    return count

def crawl_web(query: str, limit: int = 5):
    """Proxy to SearXNG for web results."""
    try:
        r = requests.get(f"http://localhost:8888/search", params={
            "q": query, "format": "json", "limit": limit
        }, timeout=10)
        if r.ok:
            return r.json().get("results", [])
    except:
        pass
    return []

# ─── Search Engine ────────────────────────────────────────────────
def search(query: str, source_type: str = None, limit: int = 20):
    start = time.time()
    query_terms = re.findall(r'\w+', query.lower())
    if not query_terms:
        return []
    if source_type:
        rows = DB.execute("SELECT * FROM search_index WHERE source_type = ?", (source_type,)).fetchall()
    else:
        rows = DB.execute("SELECT * FROM search_index").fetchall()
    results = []
    for row in rows:
        id_, source, stype, title, content, tags, url, metadata, chash, indexed_at, rel = row
        text = f"{title} {content} {tags}".lower()
        score = 0.0
        for term in query_terms:
            if term in title.lower():
                score += 10.0
            if term in tags.lower():
                score += 5.0
            count = text.count(term)
            if count > 0:
                score += min(count * 0.5, 5.0)
        if score > 0:
            results.append({
                "id": id_, "source": source, "type": stype, "title": title,
                "content": content[:300], "tags": tags, "url": url,
                "score": round(score, 2),
                "metadata": json.loads(metadata) if metadata else {},
                "indexed_at": indexed_at,
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]
    latency = int((time.time() - start) * 1000)
    DB.execute("INSERT INTO search_history (query, results_count, latency_ms, timestamp) VALUES (?,?,?,?)",
               (query, len(results), latency, datetime.now(timezone.utc).isoformat()))
    DB.commit()
    return results

def semantic_search(query: str, limit: int = 5):
    if not GROQ_KEY:
        return []
    rows = DB.execute("SELECT title, content, source, source_type, url FROM search_index LIMIT 50").fetchall()
    if not rows:
        return []
    context = "\n".join([f"[{r[2]}|{r[3]}] {r[0]}: {r[1][:200]}" for r in rows])
    prompt = f"""Given these EVEZ-OS indexed items, find the most relevant for: "{query}"
Items:\n{context}
Return JSON array: [{{"source":"","type":"","title":"","relevance":0.8,"reasoning":""}}] Max {limit} results, relevance > 0.3."""
    try:
        r = requests.post(GROQ_URL, headers={
            "Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"
        }, json={"model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 1000}, timeout=30)
        if r.ok:
            content = r.json()["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
    except:
        pass
    return []

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Search Engine", version="1.0.0")

class SearchRequest(BaseModel):
    query: str
    source_type: Optional[str] = None
    limit: int = 20
    semantic: bool = False
    live: bool = False
    web: bool = False

@app.get("/")
async def root():
    total = DB.execute("SELECT COUNT(*) FROM search_index").fetchone()[0]
    by_type = dict(DB.execute("SELECT source_type, COUNT(*) FROM search_index GROUP BY source_type").fetchall())
    return {
        "service": "EVEZ Search Engine",
        "version": "1.0.0",
        "indexed_items": total,
        "sources": list(EVEZ_SERVICES.keys()),
        "capabilities": ["keyword", "semantic", "live", "web", "github", "manifold", "research"],
    }

@app.get("/search")
async def search_get(q: str, type: Optional[str] = None, limit: int = 20,
                     semantic: bool = False, web: bool = False):
    results = search(q, source_type=type, limit=limit)
    sem = semantic_search(q) if semantic and len(results) < 3 else []
    web_results = crawl_web(q) if web else []
    return {
        "query": q, "results": results, "semantic": sem, "web": web_results,
        "total": len(results), "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/search")
async def search_post(req: SearchRequest):
    results = search(req.query, source_type=req.source_type, limit=req.limit)
    sem = semantic_search(req.query) if req.semantic and len(results) < 3 else []
    web_results = crawl_web(req.query) if req.web else []
    return {
        "query": req.query, "results": results, "semantic": sem, "web": web_results,
        "total": len(results), "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/index")
async def run_index(sources: Optional[str] = None):
    results = {}
    if not sources or "services" in (sources or "services"):
        results["services"] = crawl_services()
    if not sources or "github" in (sources or ""):
        results["github"] = crawl_github()
    if not sources or "research" in (sources or ""):
        results["research"] = crawl_research()
    if not sources or "manifolds" in (sources or ""):
        results["manifolds"] = crawl_manifolds()
    return {"indexed": results, "total_new": sum(results.values())}

@app.get("/suggest")
async def suggest(q: str, limit: int = 10):
    rows = DB.execute("SELECT DISTINCT title, source, source_type FROM search_index").fetchall()
    q_lower = q.lower()
    matches = [(t, s, st) for t, s, st in rows if q_lower in t.lower()][:limit]
    return {"suggestions": [{"title": t, "source": s, "type": st} for t, s, st in matches]}

@app.get("/graph")
async def knowledge_graph():
    nodes, edges, node_set = [], [], set()
    for row in DB.execute("SELECT source, source_type, tags, title FROM search_index").fetchall():
        source, stype, tags, title = row
        if source not in node_set:
            nodes.append({"id": source, "type": stype, "label": title[:40]})
            node_set.add(source)
        if tags:
            try:
                tag_list = json.loads(tags) if tags.startswith("[") else tags.split(",")
                for tag in tag_list:
                    tag = tag.strip().strip('"')
                    if tag and f"tag:{tag}" not in node_set:
                        nodes.append({"id": f"tag:{tag}", "type": "tag", "label": tag})
                        node_set.add(f"tag:{tag}")
                    if tag:
                        edges.append({"source": source, "target": f"tag:{tag}"})
            except:
                pass
    return {"nodes": nodes[:200], "edges": edges[:500]}

@app.get("/stats")
async def stats():
    total = DB.execute("SELECT COUNT(*) FROM search_index").fetchone()[0]
    by_type = dict(DB.execute("SELECT source_type, COUNT(*) FROM search_index GROUP BY source_type").fetchall())
    search_count = DB.execute("SELECT COUNT(*) FROM search_history").fetchone()[0]
    avg_latency = DB.execute("SELECT AVG(latency_ms) FROM search_history").fetchone()[0] or 0
    return {"indexed_items": total, "by_type": by_type, "total_searches": search_count, "avg_latency_ms": round(avg_latency,1)}

if __name__ == "__main__":
    port = int(os.getenv("EVZ_SEARCH_PORT", "8905"))
    print(f"EVEZ Search Engine on port {port}")
    try:
        n = crawl_services()
        print(f"  Pre-indexed {n} service endpoints")
    except:
        pass
    uvicorn.run(app, host="0.0.0.0", port=port)
