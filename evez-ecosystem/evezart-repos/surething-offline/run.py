"""
SureThing Offline — Entry Point
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from api.app import app
from spine.ledger import emit

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app):
    emit("system", {"mode": "offline", "version": "1.0.0"},
         operator_lane="system", subject="surething:startup", tags=["system"])

    try:
        from monitors.email_monitor import start_monitor
        start_monitor(scheduler)
    except Exception as e:
        print(f"[monitor] {e}")

    scheduler.start()
    print(f"\n\u2713 SureThing Offline running at http://localhost:{os.getenv('PORT', '8420')}")
    print(f"  Model: {os.getenv('OLLAMA_MODEL', 'mistral')}")
    print()
    yield
    scheduler.shutdown()


app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run("run:app", host=os.getenv("HOST", "0.0.0.0"),
                port=int(os.getenv("PORT", "8420")), reload=False, log_level="info")
