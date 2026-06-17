#!/usr/bin/env python3
"""
gen_video_reply.py — EVEZ-OS video reply generator (content cron entrypoint)
=============================================================================
Wrapper around gen_video_inline.py that the content cron calls.
Identical interface but named separately so cron task and inline test
can evolve independently.

Usage:
    python gen_video_reply.py --state /path/to/hyperloop_state.json \
        --output /tmp/evez_arc.mp4 --tail 20 --fps 30 --hold 2.0
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Delegate entirely to gen_video_inline — same logic, same args
from gen_video_inline import main  # noqa: F401

if __name__ == "__main__":
    # Re-exec gen_video_inline.py with same args
    import subprocess
    script = os.path.join(os.path.dirname(__file__), "gen_video_inline.py")
    result = subprocess.run([sys.executable, script] + sys.argv[1:])
    sys.exit(result.returncode)
