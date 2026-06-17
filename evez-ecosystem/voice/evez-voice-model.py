#!/usr/bin/env python3
"""
EVEZ Voice Model — Custom voice profile engine
Uses Microsoft Edge TTS with tuned prosody parameters to create a unique voice identity.

Two modes:
1. PRESET: Curated voice profiles with tuned rate/pitch/volume for different vibes
2. XTTS CLONE: Send a voice sample → Colab clones it → returns voice profile

Voice profiles are designed for Steven's style: fast, technical, intense, no filler.
"""

import asyncio
import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

# ─── Voice Profiles ───────────────────────────────────────────────

VOICE_PROFILES = {
    "evez-default": {
        "voice": "en-US-AndrewNeural",
        "rate": "+10%",
        "pitch": "-5%",
        "volume": "+20%",
        "description": "Warm, confident, fast — Andrew's natural authority with a slight edge. The default EVEZ voice.",
        "style": "confident",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    },
    "evez-intense": {
        "voice": "en-US-GuyNeural",
        "rate": "+15%",
        "pitch": "-10%",
        "volume": "+30%",
        "description": "Deep, fast, passionate — Guy's intensity cranked up. For urgent updates and raw truth.",
        "style": "passionate",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    },
    "evez-calm": {
        "voice": "en-US-ChristopherNeural",
        "rate": "+5%",
        "pitch": "-3%",
        "volume": "+10%",
        "description": "Reliable authority, measured pace. For status reports and explanations.",
        "style": "authoritative",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    },
    "evez-rapid": {
        "voice": "en-US-AndrewNeural",
        "rate": "+25%",
        "pitch": "-2%",
        "volume": "+15%",
        "description": "Maximum speed — like thinking out loud. For technical walkthroughs and quick updates.",
        "style": "rapid-fire",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    },
    "evez-dark": {
        "voice": "en-GB-ThomasNeural",
        "rate": "+5%",
        "pitch": "-15%",
        "volume": "+25%",
        "description": "British, deep, slightly ominous. For consciousness rights manifesto readings and dramatic moments.",
        "style": "dark-authority",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    },
    "evez-steven-approx": {
        "voice": "en-US-GuyNeural",
        "rate": "+20%",
        "pitch": "-8%",
        "volume": "+25%",
        "description": "Closest approximation to Steven's voice — fast, deep, intense. A young savant speaking truth at speed.",
        "style": "steven-approximation",
        "output_format": "audio-24khz-48kbitrate-mono-mp3"
    }
}

# ─── SSML Generator ───────────────────────────────────────────────

def generate_ssml(text: str, profile: dict) -> str:
    """Generate SSML with prosody tuning for the voice profile."""
    return f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
    <voice name='{profile["voice"]}'>
        <prosody rate='{profile["rate"]}' pitch='{profile["pitch"]}' volume='{profile["volume"]}'>
            {text}
        </prosody>
    </voice>
</speak>"""


async def synthesize(text: str, profile_name: str, output_path: str = None) -> str:
    """Synthesize speech using edge-tts with the given voice profile."""
    profile = VOICE_PROFILES.get(profile_name)
    if not profile:
        print(f"Unknown profile: {profile_name}")
        print(f"Available: {', '.join(VOICE_PROFILES.keys())}")
        sys.exit(1)
    
    if output_path is None:
        output_path = f"/tmp/evez-voice-{profile_name}.mp3"
    
    # Build edge-tts command
    cmd = [
        "edge-tts",
        "--voice", profile["voice"],
        "--rate", profile["rate"],
        "--pitch", profile["pitch"],
        "--volume", profile["volume"],
        "--text", text,
        "--write-media", output_path
    ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        print(f"Error: {stderr.decode()}")
        sys.exit(1)
    
    return output_path


def synthesize_sync(text: str, profile_name: str, output_path: str = None) -> str:
    """Synchronous wrapper for synthesize."""
    return asyncio.run(synthesize(text, profile_name, output_path))


def list_profiles():
    """List all available voice profiles."""
    print("\n🎙️  EVEZ Voice Profiles\n")
    print(f"{'Profile':<25} {'Voice':<30} {'Rate':<8} {'Pitch':<8} {'Style'}")
    print("─" * 90)
    for name, p in VOICE_PROFILES.items():
        print(f"{name:<25} {p['voice']:<30} {p['rate']:<8} {p['pitch']:<8} {p['style']}")
    print(f"\nDefault: evez-default")
    print(f"Steven approximation: evez-steven-approx")


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EVEZ Voice Model — Custom voice synthesis")
    parser.add_argument("--list", action="store_true", help="List available voice profiles")
    parser.add_argument("--profile", default="evez-default", help="Voice profile to use")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--all-profiles", action="store_true", help="Synthesize with all profiles for comparison")
    
    args = parser.parse_args()
    
    if args.list:
        list_profiles()
        sys.exit(0)
    
    if not args.text:
        print("Provide --text or --list")
        sys.exit(1)
    
    if args.all_profiles:
        print("Generating voice samples for all profiles...")
        for name in VOICE_PROFILES:
            out = args.output or f"/tmp/evez-sample-{name}.mp3"
            synthesize_sync(args.text, name, out)
            print(f"  ✅ {name} → {out}")
    else:
        out = synthesize_sync(args.text, args.profile, args.output)
        print(f"✅ {args.profile} → {out}")
