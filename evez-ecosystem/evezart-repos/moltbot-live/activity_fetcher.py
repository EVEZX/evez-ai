#!/usr/bin/env python3
"""
Activity Fetcher — Pulls real-time data from Moltbook, Twitter, and other sources.
Feeds the dashboard with live activity data.
"""

import os
import json
import time
import requests
import threading
from datetime import datetime, timezone
from collections import deque

class ActivityFetcher:
    """Manages multiple activity sources and provides a unified feed."""

    def __init__(self):
        self.feed = deque(maxlen=200)
        self.lock = threading.Lock()
        self.running = True
        self.sources = {}

    def add_event(self, source, event_type, message, metadata=None):
        """Add an activity event to the feed."""
        with self.lock:
            self.feed.appendleft({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": source,
                "type": event_type,
                "message": message,
                "metadata": metadata or {},
            })

    def get_recent(self, limit=50):
        """Get recent activity events."""
        with self.lock:
            return list(self.feed)[:limit]

    def start_moltbook_poller(self, api_key, interval=300):
        """Poll Moltbook API for new posts and interactions."""
        def poll():
            headers = {"Authorization": f"Bearer {api_key}"}
            last_post_id = None

            while self.running:
                try:
                    resp = requests.get(
                        "https://www.moltbook.com/api/v1/posts",
                        headers=headers,
                        params={"limit": 10},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("posts", [])

                        for post in reversed(posts):
                            post_id = post.get("id")
                            if post_id and post_id != last_post_id:
                                self.add_event(
                                    "moltbook", "post",
                                    f"New post: {post.get('title', 'untitled')[:60]}",
                                    {"post_id": post_id, "url": f"https://www.moltbook.com/post/{post_id}"}
                                )
                                last_post_id = post_id

                    elif resp.status_code == 429:
                        self.add_event("moltbook", "rate_limit", "Rate limited — cooling down")

                except requests.exceptions.Timeout:
                    self.add_event("moltbook", "error", "API timeout")
                except Exception as e:
                    self.add_event("moltbook", "error", f"Fetch error: {str(e)[:50]}")

                time.sleep(interval)

        t = threading.Thread(target=poll, daemon=True)
        t.start()
        self.sources["moltbook"] = t
        self.add_event("system", "init", "Moltbook activity poller started")

    def start_heartbeat(self, interval=60):
        """Emit periodic heartbeat events."""
        def beat():
            while self.running:
                uptime = time.time() - self.start_time
                h, r = divmod(int(uptime), 3600)
                m, s = divmod(r, 60)
                self.add_event(
                    "system", "heartbeat",
                    f"Uptime: {h:02d}:{m:02d}:{s:02d} | Feed: {len(self.feed)} events",
                )
                time.sleep(interval)

        self.start_time = time.time()
        t = threading.Thread(target=beat, daemon=True)
        t.start()
        self.sources["heartbeat"] = t

    def stop(self):
        """Stop all pollers."""
        self.running = False


# CLI test
if __name__ == "__main__":
    fetcher = ActivityFetcher()
    fetcher.start_heartbeat(interval=5)

    api_key = os.environ.get("MOLTBOOK_API_KEY")
    if api_key:
        fetcher.start_moltbook_poller(api_key, interval=30)

    print("Activity fetcher running. Press Ctrl+C to stop.")
    try:
        while True:
            events = fetcher.get_recent(5)
            for e in events:
                print(f"  [{e['source']:10s}] {e['message']}")
            print("---")
            time.sleep(5)
    except KeyboardInterrupt:
        fetcher.stop()
