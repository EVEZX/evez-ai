#!/usr/bin/env python3
"""
EVEZ Vocaloid Engine — Free singing voice synthesis
Combines Edge TTS (speaking) + RVC voice conversion (singing) + XTTS cloning (identity)

Pipeline:
1. Text → Edge TTS → base audio (any voice, any prosody)
2. Base audio → RVC model → YOUR voice singing/speaking
3. Voice sample → XTTS v2 → voice clone for generation

This runs the speaking side on VPS (free).
The training/cloning side runs on Colab (free T4 GPU).
"""

import subprocess
import json
import os
import sys
import tempfile
from pathlib import Path

VOICE_MODEL_DIR = Path(__file__).parent
VOICE_MODEL_JSON = VOICE_MODEL_DIR / "voice-model.json"

# Load voice profiles
with open(VOICE_MODEL_JSON) as f:
    MODEL = json.load(f)

PROFILES = MODEL["profiles"]
ACTIVE = MODEL.get("active_profile", "evez-default")


def get_profile(name: str = None) -> dict:
    name = name or ACTIVE
    if name not in PROFILES:
        print(f"Unknown profile: {name}. Available: {', '.join(PROFILES.keys())}")
        sys.exit(1)
    return PROFILES[name]


def synthesize(text: str, profile_name: str = None, output_path: str = None) -> str:
    """Synthesize speech using edge-tts with a voice profile."""
    profile = get_profile(profile_name)
    output_path = output_path or tempfile.mktemp(suffix=".mp3")
    
    cmd = [
        "edge-tts",
        f"--voice={profile['voice']}",
        f"--rate={profile['rate']}",
        f"--pitch={profile['pitch']}",
        f"--volume={profile['volume']}",
        "-t", text,
        f"--write-media={output_path}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return output_path


def synthesize_singing(midi_or_vocal: str, rvc_model: str, output_path: str = None,
                       transpose: int = 0, pitch_method: str = "crepe") -> str:
    """
    Convert a vocal/instrumental track to EVEZ voice using RVC.
    Requires a trained .pth model from the Colab vocaloid notebook.
    
    This is a placeholder — actual RVC inference needs GPU.
    On VPS, we prepare the inputs. On Colab, we run the conversion.
    """
    output_path = output_path or tempfile.mktemp(suffix=".wav")
    
    # Prepare conversion job for Colab
    job = {
        "input": midi_or_vocal,
        "model": rvc_model,
        "output": output_path,
        "transpose": transpose,
        "pitch_method": pitch_method,
        "profile": ACTIVE
    }
    
    job_path = output_path.replace(".wav", ".job.json")
    with open(job_path, 'w') as f:
        json.dump(job, f, indent=2)
    
    print(f"📦 Conversion job saved: {job_path}")
    print(f"   Run this job on Colab with the EVEZ Vocaloid notebook")
    return job_path


def list_voices():
    print("\n🎤 EVEZ Voice Profiles\n")
    for name, p in PROFILES.items():
        marker = " ← ACTIVE" if name == ACTIVE else ""
        print(f"  {name}{marker}")
        print(f"    Voice: {p['voice']} | Rate: {p['rate']} | Pitch: {p['pitch']} | Style: {p['style']}")
        print(f"    {p['description']}")
        print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EVEZ Vocaloid Engine")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--speak", help="Text to speak")
    parser.add_argument("--profile", default=ACTIVE)
    parser.add_argument("--output", help="Output path")
    parser.add_argument("--sing", help="Vocal track to convert (for Colab)")
    parser.add_argument("--model", help="RVC .pth model path")
    
    args = parser.parse_args()
    
    if args.list:
        list_voices()
    elif args.speak:
        out = synthesize(args.speak, args.profile, args.output)
        print(f"✅ {args.profile} → {out}")
    elif args.sing and args.model:
        synthesize_singing(args.sing, args.model, args.output)
    else:
        list_voices()
