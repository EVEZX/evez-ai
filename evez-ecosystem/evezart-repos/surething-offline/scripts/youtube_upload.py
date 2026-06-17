#!/usr/bin/env python3
"""EVEZ YouTube Upload. Channel @lordevez (UCozc0hUiPxhhYD3hP6GVbIQ)
Env: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN"""
from __future__ import annotations
import argparse, json, os, sys
import requests
from pathlib import Path

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status"
CHANNEL_ID = "UCozc0hUiPxhhYD3hP6GVbIQ"

def refresh(cid, cs, rt):
    r = requests.post(TOKEN_URL, data={"client_id":cid,"client_secret":cs,"refresh_token":rt,"grant_type":"refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]

def upload(video_path, meta, token):
    body = json.dumps({"snippet":{"title":meta["title"],"description":meta["description"],
        "tags":meta.get("tags",[]),"categoryId":meta.get("categoryId","28")},
        "status":{"privacyStatus":meta.get("privacyStatus","public")}})
    b = "evez_bnd"
    with open(video_path,"rb") as f: vid = f.read()
    parts = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{body}\r\n--{b}\r\nContent-Type: video/mp4\r\n\r\n").encode() + vid + f"\r\n--{b}--".encode()
    r = requests.post(UPLOAD_URL, data=parts, headers={"Authorization":f"Bearer {token}","Content-Type":f"multipart/related; boundary={b}"})
    r.raise_for_status()
    return r.json()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--composio", action="store_true")
    args = p.parse_args()
    meta = json.loads(Path(args.metadata).read_text()) if Path(args.metadata).exists() else {}
    if not Path(args.video).exists(): print(f"Video not found: {args.video}"); sys.exit(1)
    if args.composio:
        print("Composio: YOUTUBE_MULTIPART_UPLOAD_VIDEO")
        print(json.dumps({"channel": CHANNEL_ID, "metadata": meta})); sys.exit(0)
    cid,cs,rt = os.environ.get("YOUTUBE_CLIENT_ID"),os.environ.get("YOUTUBE_CLIENT_SECRET"),os.environ.get("YOUTUBE_REFRESH_TOKEN")
    if not all([cid,cs,rt]): print("Missing YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN"); sys.exit(1)
    token = refresh(cid,cs,rt)
    result = upload(args.video, meta, token)
    vid = result.get("id")
    url = f"https://www.youtube.com/watch?v={vid}"
    print(f"Uploaded: {url}")
    print(json.dumps({"video_id":vid,"url":url,"title":meta.get("title")}))

if __name__ == "__main__": main()
