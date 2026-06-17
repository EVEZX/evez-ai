#!/usr/bin/env python3
"""
EVEZ Mesh Broker — Full implementation with pub/sub, queue, and health tracking.
Port 8894
"""
import json, time, asyncio, hashlib, os
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="EVEZ Mesh Broker", version="2.0.0")

BROKER_PORT = int(os.getenv("BROKER_PORT", "8894"))
START_TIME = time.time()

class Message(BaseModel):
    topic: str
    payload: Any
    sender: str = "unknown"
    priority: int = 5  # 1=highest, 10=lowest

class Subscription(BaseModel):
    subscriber_id: str
    callback_url: str
    topics: List[str]

# ── State ───────────────────────────────────────────────────────
queues: Dict[str, List[Dict]] = {}          # topic → [messages]
subscribers: Dict[str, Subscription] = {}  # sub_id → Subscription
dead_letter: List[Dict] = []               # failed deliveries
stats = {"published": 0, "delivered": 0, "failed": 0}

# ── Pub/Sub ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "evez-mesh-broker",
        "uptime_s": round(time.time() - START_TIME, 1),
        "queues": len(queues),
        "subscribers": len(subscribers),
        "stats": stats
    }

@app.post("/broker/pub")
async def publish(msg: Message):
    """Publish a message to a topic"""
    if msg.topic not in queues:
        queues[msg.topic] = []
    
    envelope = {
        "id": hashlib.sha256(f"{msg.topic}{msg.payload}{time.time()}".encode()).hexdigest()[:12],
        "topic": msg.topic,
        "payload": msg.payload,
        "sender": msg.sender,
        "priority": msg.priority,
        "ts": time.time(),
        "delivered_to": []
    }
    queues[msg.topic].append(envelope)
    queues[msg.topic].sort(key=lambda x: x["priority"])
    stats["published"] += 1
    
    # Deliver to subscribers
    delivered = 0
    async with httpx.AsyncClient(timeout=5) as client:
        for sub in subscribers.values():
            if msg.topic in sub.topics or "*" in sub.topics:
                try:
                    await client.post(sub.callback_url, json=envelope)
                    envelope["delivered_to"].append(sub.subscriber_id)
                    delivered += 1
                    stats["delivered"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    dead_letter.append({**envelope, "error": str(e), "sub": sub.subscriber_id})
    
    return {"id": envelope["id"], "topic": msg.topic, "delivered_to": delivered}

@app.get("/broker/sub/{topic}")
def pull_messages(topic: str, limit: int = 10):
    """Pull messages from a topic queue"""
    msgs = queues.get(topic, [])[:limit]
    return {"topic": topic, "messages": msgs, "count": len(msgs)}

@app.post("/broker/subscribe")
def subscribe(sub: Subscription):
    """Register a callback subscriber"""
    subscribers[sub.subscriber_id] = sub
    return {"subscriber_id": sub.subscriber_id, "topics": sub.topics}

@app.delete("/broker/subscribe/{sub_id}")
def unsubscribe(sub_id: str):
    if sub_id not in subscribers:
        raise HTTPException(404, "Subscriber not found")
    del subscribers[sub_id]
    return {"unsubscribed": sub_id}

@app.get("/broker/status")
def broker_status():
    return {
        "queue_topics": list(queues.keys()),
        "queue_depths": {t: len(v) for t, v in queues.items()},
        "subscribers": len(subscribers),
        "dead_letter_count": len(dead_letter),
        "stats": stats,
        "uptime_s": round(time.time() - START_TIME, 1)
    }

@app.get("/broker/dead-letter")
def get_dead_letter(limit: int = 20):
    return {"dead_letter": dead_letter[-limit:], "total": len(dead_letter)}

@app.delete("/broker/queue/{topic}")
def clear_queue(topic: str):
    cleared = len(queues.get(topic, []))
    queues[topic] = []
    return {"topic": topic, "cleared": cleared}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BROKER_PORT)
