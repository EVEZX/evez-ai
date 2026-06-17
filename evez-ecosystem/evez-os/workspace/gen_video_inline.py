#!/usr/bin/env python3
"""
gen_video_inline.py — EVEZ-OS Canonical Video Generator
Alias/wrapper for PIL+ffmpeg inline render pattern.
Delegates to gen_video_reply.py for full-arc mode.
For quick inline renders, see the PIL+ffmpeg pattern used in the content cron.

Usage:
    python gen_video_inline.py --state /path/to/hyperloop_state.json --output /tmp/evez_arc.mp4
    python gen_video_inline.py --state /path/to/state.json --output /tmp/arc.mp4 --tail 20 --fps 30 --hold 1.5
"""
import sys, os, subprocess, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--tail', type=int, default=20)
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--hold', type=float, default=1.5)
    args = parser.parse_args()

    # Delegate to gen_video_reply.py (full-arc renderer)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reply_script = os.path.join(script_dir, 'gen_video_reply.py')
    if os.path.exists(reply_script):
        cmd = [sys.executable, reply_script, '--state', args.state, '--output', args.output]
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    else:
        print(f"ERROR: gen_video_reply.py not found at {reply_script}")
        print("Use PIL+ffmpeg inline pattern from content cron instead.")
        sys.exit(1)

if __name__ == '__main__':
    main()
