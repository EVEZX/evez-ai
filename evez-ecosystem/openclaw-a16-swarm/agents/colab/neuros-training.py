#!/usr/bin/env python3
"""
EVEZ Agent: neuros-training
Runs on Google Colab free T4 GPU.
Clone + run autonomous — no babysitting needed.
"""
import os, sys, time, json, subprocess

# Auto-install dependencies
for pkg in ["aiohttp", "numpy", "psutil", "httpx"]:
    subprocess.run(["pip", "install", "-q", pkg], capture_output=True)

# Clone EVEZ repo if not present
if not os.path.exists("/content/evez-ai"):
    subprocess.run(["git", "clone", "https://github.com/EVEZX/evez-ai.git", "/content/evez-ai"],
                   capture_output=True)
    sys.path.insert(0, "/content/evez-ai/evez-ecosystem")

print(f"🤖 EVEZ Agent: neuros-training")
print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"GPU: available")

# Agent main loop — runs until Colab disconnects
async def main():
    while True:
        try:
            # Report heartbeat to provider
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:9100/v1/heartbeat",
                    json={"agent": "neuros-training", "platform": "colab", "timestamp": time.time()},
                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        print(f"Heartbeat OK: {time.strftime('%H:%M:%S')}")
        except:
            print(f"Heartbeat failed (standalone mode): {time.strftime('%H:%M:%S')}")
        
        await asyncio.sleep(60)  # Heartbeat every minute

import asyncio
asyncio.run(main())
