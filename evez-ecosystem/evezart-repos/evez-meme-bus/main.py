"""
EVEZ Meme Bus — main entrypoint.
Boots all agents and the FireSync loop in threads.
FastAPI served via: uvicorn service.api:app --host 0.0.0.0 --port 8000
"""
import threading, time

from agents import (
    image_ingestor, twitter_context, corpus_agent,
    caption_agent, guard_agent, layout_agent,
    publisher, vision_agent, audio_narrator,
    twitter_poster, spine_bridge
)
from loops import fire_sync

def boot():
    # Wire all event subscriptions
    vision_agent.start()
    caption_agent.start()
    guard_agent.start()
    layout_agent.start()
    publisher.start()
    audio_narrator.start()
    twitter_poster.start()
    spine_bridge.start()

    # Start polling loops in daemon threads
    loops = [
        (image_ingestor.run_poll_loop,   {"interval_sec": 60}),
        (twitter_context.run_poll_loop,  {"interval_sec": 300}),
        (corpus_agent.run_poll_loop,     {"interval_sec": 600}),
        (fire_sync.run_poll_loop,        {"interval_sec": 120}),
    ]
    for fn, kwargs in loops:
        t = threading.Thread(target=fn, kwargs=kwargs, daemon=True)
        t.start()
        print(f"[main] started {fn.__module__}.{fn.__name__}")

    print("[main] EVEZ Meme Bus v2 live. Drop images → assets/input_images/")
    print("[main] FastAPI: uvicorn service.api:app --host 0.0.0.0 --port 8000")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[main] shutdown")

if __name__ == "__main__":
    boot()
