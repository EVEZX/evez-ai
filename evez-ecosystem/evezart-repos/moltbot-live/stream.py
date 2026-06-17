#!/usr/bin/env python3
"""
MoltBot Live Stream — FFmpeg RTMP Orchestrator
Launches xvfb + dashboard + FFmpeg pipeline to stream to YouTube Live.
"""

import os
import sys
import signal
import subprocess
import time
import argparse
import atexit

# ── Configuration ────────────────────────────────────────────
DISPLAY = os.environ.get("STREAM_DISPLAY", ":99")
WIDTH = os.environ.get("RESOLUTION", "1280x720").split("x")[0]
HEIGHT = os.environ.get("RESOLUTION", "1280x720").split("x")[1]
FPS = os.environ.get("FPS", "30")
BITRATE = os.environ.get("BITRATE", "2500k")
YOUTUBE_RTMP_URL = os.environ.get("YOUTUBE_RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
YOUTUBE_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")

processes = []

def cleanup():
    """Kill all child processes on exit."""
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            try:
                p.kill()
            except:
                pass
    print("[stream] All processes cleaned up.")

atexit.register(cleanup)

def signal_handler(sig, frame):
    print(f"\n[stream] Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_xvfb():
    """Start virtual framebuffer."""
    print(f"[stream] Starting Xvfb on {DISPLAY} at {WIDTH}x{HEIGHT}...")
    cmd = [
        "Xvfb", DISPLAY,
        "-screen", "0", f"{WIDTH}x{HEIGHT}x24",
        "-ac",
        "+extension", "GLX",
        "+render",
        "-noreset",
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    processes.append(p)
    time.sleep(1)

    if p.poll() is not None:
        print("[stream] ERROR: Xvfb failed to start!")
        sys.exit(1)

    os.environ["DISPLAY"] = DISPLAY
    print(f"[stream] Xvfb running on {DISPLAY}")
    return p

def start_dashboard():
    """Launch the EVEZ OS agent POV dashboard."""
    print("[stream] Starting EVEZ OS dashboard...")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    env["STREAM_WIDTH"] = WIDTH
    env["STREAM_HEIGHT"] = HEIGHT

    p = subprocess.Popen(
        [sys.executable, "dashboard_evez.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(p)
    time.sleep(2)

    if p.poll() is not None:
        stderr = p.stderr.read().decode()
        print(f"[stream] ERROR: Dashboard failed to start!\n{stderr}")
        sys.exit(1)

    print("[stream] EVEZ OS dashboard running.")
    return p

def start_ffmpeg(preview=False):
    """Start FFmpeg capture and RTMP stream."""
    rtmp_url = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

    cmd = [
        "ffmpeg",
        "-y",
        # Video input: X11 screen capture
        "-f", "x11grab",
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", FPS,
        "-i", DISPLAY,
        # Audio: silent audio track (YouTube requires audio)
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        # Video encoding
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-level", "4.1",
        "-b:v", BITRATE,
        "-maxrate", BITRATE,
        "-bufsize", str(int(BITRATE.replace("k", "")) * 2) + "k",
        "-g", str(int(FPS) * 2),  # Keyframe every 2 sec
        "-keyint_min", FPS,
        "-pix_fmt", "yuv420p",
        # Audio encoding
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        # Output
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
    ]

    if preview:
        # Output to local file for testing
        cmd.append("preview_output.flv")
        print("[stream] FFmpeg capturing to preview_output.flv")
    else:
        cmd.append(rtmp_url)
        print(f"[stream] FFmpeg streaming to YouTube Live...")

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(p)
    time.sleep(3)

    if p.poll() is not None:
        stderr = p.stderr.read().decode()
        print(f"[stream] ERROR: FFmpeg failed!\n{stderr[:500]}")
        sys.exit(1)

    print("[stream] FFmpeg encoding and streaming.")
    return p

def monitor(dashboard_proc, ffmpeg_proc):
    """Monitor processes and restart if they crash."""
    print("[stream] \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")
    print("[stream] \u25cf EVEZ OS LIVE \u2014 STREAMING")
    print("[stream] \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550")

    while True:
        # Check dashboard
        if dashboard_proc.poll() is not None:
            print("[stream] WARNING: Dashboard crashed! Restarting...")
            dashboard_proc = start_dashboard()

        # Check FFmpeg
        if ffmpeg_proc.poll() is not None:
            print("[stream] WARNING: FFmpeg crashed! Restarting...")
            time.sleep(5)
            ffmpeg_proc = start_ffmpeg()

        # Heartbeat
        time.sleep(10)

def main():
    parser = argparse.ArgumentParser(description="EVEZ OS Live Stream")
    parser.add_argument("--preview", action="store_true", help="Preview mode (no YouTube stream)")
    parser.add_argument("--no-xvfb", action="store_true", help="Skip Xvfb (use existing display)")
    args = parser.parse_args()

    if not args.preview and not YOUTUBE_STREAM_KEY:
        print("[stream] ERROR: YOUTUBE_STREAM_KEY not set!")
        print("[stream] Set it in .env or export YOUTUBE_STREAM_KEY=xxxx")
        sys.exit(1)

    # Start the pipeline
    if not args.no_xvfb:
        start_xvfb()
    else:
        os.environ.setdefault("DISPLAY", DISPLAY)

    dashboard_proc = start_dashboard()
    ffmpeg_proc = start_ffmpeg(preview=args.preview)

    # Monitor forever
    try:
        monitor(dashboard_proc, ffmpeg_proc)
    except KeyboardInterrupt:
        print("\n[stream] Shutting down...")
        cleanup()

if __name__ == "__main__":
    main()
