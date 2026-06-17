#!/usr/bin/env python3
"""
EVEZ FIRE Video Upload to YouTube
Downloads presigned MP4 from Veo 3 render, uploads to @lordevez

Called by GitHub Actions fire-video-upload CI.
"""
import os, sys, json, tempfile, requests

VIDEO_URL  = os.environ.get("VIDEO_URL", "")
ROUND      = os.environ.get("ROUND", "0")
TAU        = os.environ.get("TAU", "0")
FIRE_TYPE  = os.environ.get("FIRE_TYPE", "FIRE")

title = f"FIRE #{ROUND} \u2014 \u03c4={TAU} | EVEZ OS live cognition | {FIRE_TYPE}"
description = f"""EVEZ OS FIRE event \u2014 Round {ROUND}

\u03c4 (tau) = {TAU} | Type: {FIRE_TYPE}

The EVEZ OS EventSpine crossed the FIRE threshold.

EVEZ OS is an autonomous cognitive system that runs a continuous hyperloop
computing FIRE thresholds from a live topology of distinct prime factors.
Every round either fires or holds \u2014 the outcome is mathematically determined,
not predicted. This is the record. \u25ca

Architecture:
  EventSpine \u2192 CPF GateLock \u2192 FIRE/NO_FIRE \u2192 Spine Append \u2192 Veo 3 Render \u2192 Upload

EVEZ OS: https://github.com/EvezArt/evez-os
@EVEZ666 on Twitter | @lordevez on YouTube
"""

tags = [
    "EVEZ", "EVEZOS", "AI", "autonomous agent", "live cognition",
    "EventSpine", "FIRE", f"round{ROUND}", f"tau{TAU}",
    "hyperloop", "CPF", "prime factors", "math"
]

if not VIDEO_URL:
    print("ERROR: VIDEO_URL not set")
    sys.exit(1)

print(f"Downloading video...")
resp = requests.get(VIDEO_URL, stream=True, timeout=120)
resp.raise_for_status()

tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
for chunk in resp.iter_content(chunk_size=8192):
    tmp.write(chunk)
tmp.close()
print(f"Downloaded: {os.path.getsize(tmp.name):,} bytes")

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

token_json = os.environ.get("YOUTUBE_TOKEN")
if not token_json:
    print("ERROR: YOUTUBE_TOKEN secret not set")
    sys.exit(1)

creds = Credentials.from_authorized_user_info(json.loads(token_json))
youtube = build("youtube", "v3", credentials=creds)

body = {
    "snippet": {
        "title": title,
        "description": description,
        "tags": tags,
        "categoryId": "28",
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
    }
}

media = MediaFileUpload(tmp.name, mimetype="video/mp4", resumable=True, chunksize=1024*1024)
print(f"Uploading: {title}")
request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"  {int(status.progress() * 100)}%")

video_id = response["id"]
print(f"\n\u2713 UPLOADED: https://youtu.be/{video_id}")

with open("fire_upload_result.json", "w") as f:
    json.dump({
        "video_id": video_id,
        "watch_url": f"https://youtu.be/{video_id}",
        "title": title,
        "round": ROUND,
        "tau": TAU,
        "fire_type": FIRE_TYPE,
    }, f, indent=2)

os.unlink(tmp.name)
