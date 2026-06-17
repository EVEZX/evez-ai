#!/usr/bin/env python3
"""
BRUTAL Twitter Meme Agent - POSTS IMMEDIATELY
"""
import subprocess

MEMES = [
    "Market just got rug pulled. EvezVearl protocol activated. #EVEZ #evez666",
    "CAIN contradiction engine running hot. 0.99Φ achieved. Reality unstable. #EVEZ",
    "Noclip mode engaged. God Circuit approves. #evez666",
]

for meme in MEMES:
    subprocess.run(["xurl", "post", meme])
    print(f"Sent: {meme[:40]}...")