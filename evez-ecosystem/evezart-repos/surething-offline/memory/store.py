"""
SureThing Offline — Memory Layer (Chroma)
"""
from __future__ import annotations
import os, uuid
from pathlib import Path
from typing import Optional

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
_client = None
_collection = None

def _get_collection():
    global _client, _collection
    if _collection: return _collection
    try:
        import chromadb
        Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection("surething_memory")
        return _collection
    except: return None

def save(content, category="general", metadata=None):
    coll = _get_collection()
    if not coll: return "[memory unavailable]"
    mid = str(uuid.uuid4())
    coll.add(documents=[content], ids=[mid], metadatas=[{"category": category, **(metadata or {})}])
    return mid

def search(query, category=None, n_results=5):
    coll = _get_collection()
    if not coll: return []
    try:
        r = coll.query(query_texts=[query], n_results=n_results,
                       where={"category": category} if category else None)
        docs = r.get("documents",[[]])[0]; metas = r.get("metadatas",[[]])[0]; ids = r.get("ids",[[]])[0]
        return [{"id":ids[i],"content":docs[i],"metadata":metas[i]} for i in range(len(docs))]
    except: return []

def delete(mem_id):
    coll = _get_collection()
    if not coll: return False
    try: coll.delete(ids=[mem_id]); return True
    except: return False

def health():
    coll = _get_collection()
    count = 0
    if coll:
        try: count = coll.count()
        except: pass
    return {"available": coll is not None, "persist_dir": CHROMA_PERSIST_DIR, "memory_count": count}
