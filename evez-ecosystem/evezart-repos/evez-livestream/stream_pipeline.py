"""
EVEZ Stream Pipeline — ffmpeg RTMP pipeline + YouTube Live API
Generates audio from breakcore engine, creates visualization, pushes to YouTube via RTMP.
"""
import os, sys, json, time, threading, subprocess, requests
from datetime import datetime, timezone, timedelta

# ─── Config ────────────────────────────────────────────────────────
YOUTUBE_ACCOUNT = "youtube_aka-racker"  # Steven Maggard channel
COMPOSIO_API_KEY = "ck_nGR0xHdPC0mRYoxmoHUo"
COMPOSIO_USER_KEY = "uak_SYJGzjHTldgwjrUEzE3G"

# ─── YouTube Live API via Composio proxy ───────────────────────────
class YouTubeLiveAPI:
    """Create and manage YouTube live broadcasts via the Data API through Composio."""
    
    BASE = "https://api.composio.dev"
    
    def __init__(self, account_id=YOUTOUTUBE_ACCOUNT):
        self.account_id = account_id
    
    def _call(self, method, endpoint, body=None):
        """Call YouTube Data API via Composio proxy_execute or direct API."""
        headers = {
            "x-consumer-api-key": COMPOSIO_API_KEY,
            "Content-Type": "application/json"
        }
        url = f"{self.BASE}/v1/connectedAccounts/{self.account_id}/execute/youtube_{endpoint}"
        # Use direct YouTube API via requests with OAuth token from Composio
        # For now, we'll use the liveBroadcasts insert via Composio
        pass
    
    def create_broadcast(self, title, description="", start_time=None, privacy="public"):
        """Create a liveBroadcast resource."""
        if start_time is None:
            start_time = datetime.now(timezone.utc).isoformat()
        
        # Use Composio YOUTUBE tools or direct API
        # Since Composio doesn't have liveBroadcasts insert, we use direct YouTube Data API
        # through the authenticated connection
        return {
            "snippet": {
                "title": title,
                "description": description,
                "scheduledStartTime": start_time,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
            "contentDetails": {
                "enableAutoStart": True,
                "enableAutoStop": False,
                "monitorStream": {
                    "enableMonitorStream": False,
                }
            }
        }


# ─── RTMP Pipeline ────────────────────────────────────────────────
class RTMPPipeline:
    """Pipe breakcore audio + visualization to YouTube via ffmpeg RTMP."""
    
    def __init__(self, rtmp_url, stream_key, breakcore_port=8896):
        self.rtmp_url = rtmp_url
        self.stream_key = stream_key
        self.full_url = f"{rtmp_url}/{stream_key}"
        self.breakcore_port = breakcore_port
        self.ffmpeg = None
        self.running = False
    
    def start(self):
        """Start ffmpeg pipeline: audio from breakcore + generate video frames → RTMP."""
        self.running = True
        
        # ffmpeg command:
        # -re: read at native framerate
        # -i pipe:0: audio from stdin
        # -f image2pipe: video frames from another input
        # -c:v libx264: H.264 video codec
        # -c:a aac: AAC audio codec
        # -f flv: FLV container for RTMP
        
        cmd = [
            "ffmpeg",
            "-y",
            # Audio input (from breakcore WAV stream)
            "-i", f"http://localhost:{self.breakcore_port}/stream",
            # Video: generate a test pattern (we'll replace with real viz)
            "-f", "lavfi", "-i", f"color=c=0x0a0014:s=1920x1080:r=2",
            # Video codec
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-b:v", "2500k",
            "-maxrate", "2500k",
            "-bufsize", "5000k",
            "-pix_fmt", "yuv420p",
            "-g", "4",
            # Audio codec
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            # Output format
            "-f", "flv",
            self.full_url
        ]
        
        self.ffmpeg = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return self.ffmpeg
    
    def stop(self):
        if self.ffmpeg:
            self.ffmpeg.terminate()
            self.ffmpeg.wait(timeout=5)
        self.running = False


# ─── YouTube Stream Setup Instructions ────────────────────────────
def print_setup_instructions():
    """Print instructions for manually setting up YouTube live streams."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  ⚡ EVEZ 404 BREAKCORE — YouTube Live Setup                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. Go to YouTube Studio → Go Live                              ║
║  2. Create these streams:                                        ║
║                                                                  ║
║  ⚡ 404 Breakcore (music stream)                                 ║
║     - Category: Music                                            ║
║     - Title: ⚡ 404 BREAKCORE — AI Generative Breakcore 24/7     ║
║     - Stream key → set in RTMPPipeline                          ║
║                                                                  ║
║  🧠 EVEZ Cognition Forensics (visualizer)                       ║
║     - Category: Science & Technology                             ║
║     - Title: 🧠 EVEZ Cognition — AI Forensics Live              ║
║                                                                  ║
║  🏭 EVEZ Factory AI Builder (visualizer)                        ║
║     - Category: Science & Technology                             ║
║     - Title: 🏭 EVEZ Factory — AI That Builds AI (LIVE)         ║
║                                                                  ║
║  🕸️ EVEZ Mesh Brain Network (visualizer)                        ║
║     - Category: Science & Technology                             ║
║     - Title: 🕸️ EVEZ Mesh — Decentralized AI Brain Network      ║
║                                                                  ║
║  3. Get stream keys and pass to:                                 ║
║     curl -X POST localhost:8896/api/start_stream \\              ║
║       -d '{"rtmp_url":"a.rtmp.youtube.com/live2",               ║
║             "stream_key":"xxxx-xxxx-xxxx-xxxx"}'                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    print_setup_instructions()
