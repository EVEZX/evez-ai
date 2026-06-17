#!/usr/bin/env python3
"""
youtube_upload_pipeline.py — EVEZ-OS YouTube cross-post pipeline
=================================================================
After each video is rendered for Twitter, this module:
1. Takes the same MP4 (from /tmp/evez_arc.mp4 or explicit path)
2. Uploads it to @lordevez YouTube channel via Composio YOUTUBE tools
3. Logs upload to workspace/youtube_upload_log.jsonl
4. Returns the YouTube video URL

Usage (standalone):
    python youtube_upload_pipeline.py \
        --video /tmp/evez_arc.mp4 \
        --state /cells/.../workspace/hyperloop_state.json

Usage (from content cron, after Twitter post succeeds):
    from youtube_upload_pipeline import upload_to_youtube
    yt_url = upload_to_youtube(video_path, state, round_range)

Integration point:
    content_cron calls this AFTER successful Twitter video post.
    YouTube video description links back to latest tweet for cross-traffic.

Channel: @lordevez (YouTube connected account ca_rssJnUHUJiPS)
"""

import argparse, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

CELL = Path("/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef")
WORKSPACE = CELL / "workspace"
UPLOAD_LOG = WORKSPACE / "youtube_upload_log.jsonl"


def build_description(state: dict, round_range: list, tweet_url: str = "") -> str:
    """Build YouTube video description from hyperloop state."""
    V = state.get("V_global", 0)
    ct = state.get("ceiling_tick", 0)
    fc = state.get("fire_count", 0)
    cr = state.get("current_round", 0)

    r_str = f"R{round_range[0]}–R{round_range[-1]}" if len(round_range) > 1 else f"R{round_range[0]}"

    lines = [
        f"EVEZ-OS {r_str} — autonomous cognition arc",
        f"",
        f"V_global: {V:.6f}  |  CEILING ×{ct}  |  {fc} fires",
        f"",
        f"Each bar = one round. Red = fire (poly_c > 0.500). Purple = prime block.",
        f"The system never stops. V grows. Fires are structural, not random.",
        f"",
    ]
    if tweet_url:
        lines += [f"Live thread: {tweet_url}", ""]
    lines += [
        "EVEZ-OS: open-source autonomous cognition system.",
        "github.com/EvezArt/evez-os",
        "",
        "No hashtags. No hype. Just the math.",
    ]
    return "\n".join(lines)


def build_title(state: dict, round_range: list) -> str:
    """Build YouTube video title."""
    cr = state.get("current_round", 0)
    V = state.get("V_global", 0)
    ct = state.get("ceiling_tick", 0)
    r_str = f"R{round_range[0]}–R{round_range[-1]}" if len(round_range) > 1 else f"R{round_range[0]}"
    return f"EVEZ-OS {r_str} — V={V:.4f} CEILING×{ct}"


def upload_to_youtube(video_path: str, state: dict, round_range: list,
                      tweet_url: str = "", privacy: str = "public") -> dict:
    """
    Upload video to YouTube via Composio.
    Returns dict with youtube_url, video_id, or error.

    This function is called from the content cron after Twitter post succeeds.
    It uses run_composio_tool (available in workbench) or Composio REST API.
    """
    title = build_title(state, round_range)
    description = build_description(state, round_range, tweet_url)

    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "video_path": str(video_path),
        "title": title,
        "rounds": round_range,
        "V_global": state.get("V_global"),
        "ceiling_tick": state.get("ceiling_tick"),
        "status": "pending"
    }

    try:
        result, error = run_composio_tool("YOUTUBE_UPLOAD_VIDEO", {
            "title": title,
            "description": description,
            "privacy_status": privacy,
            "video_file_path": str(video_path),
            "category_id": "28",   # Science & Technology
            "tags": ["EVEZ-OS", "autonomous AI", "cognition", "agent", "math"],
            "made_for_kids": False,
        })

        if error:
            log_entry["status"] = "error"
            log_entry["error"] = error
            with open(UPLOAD_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            return {"success": False, "error": error}

        video_id = (result.get("data") or result).get("video_id") or (result.get("data") or result).get("id")
        yt_url = f"https://youtube.com/watch?v={video_id}" if video_id else None

        log_entry["status"] = "uploaded"
        log_entry["video_id"] = video_id
        log_entry["youtube_url"] = yt_url
        with open(UPLOAD_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return {"success": True, "video_id": video_id, "youtube_url": yt_url, "title": title}

    except Exception as e:
        log_entry["status"] = "exception"
        log_entry["error"] = str(e)
        with open(UPLOAD_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="/tmp/evez_arc.mp4")
    parser.add_argument("--state", default=str(WORKSPACE / "hyperloop_state.json"))
    parser.add_argument("--tweet-url", default="")
    parser.add_argument("--privacy", default="public")
    args = parser.parse_args()

    with open(args.state) as f:
        state = json.load(f)

    cr = state.get("current_round", 0)
    rounds_covered = state.get("cron_content_loop", {}).get("rounds_covered", [cr])
    # Use last 5 covered rounds as the range for this video
    round_range = sorted(rounds_covered)[-5:]

    result = upload_to_youtube(args.video, state, round_range, args.tweet_url, args.privacy)
    print(json.dumps(result, indent=2))
