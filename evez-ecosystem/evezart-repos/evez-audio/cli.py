#!/usr/bin/env python3
"""EVEZ Audio Engine CLI — procedural cognitohazard synthesis"""
import sys
import argparse
from evez_audio.engine import *

def main():
    parser = argparse.ArgumentParser(description="EVEZ Audio Engine — Cognitohazard Synthesis")
    parser.add_argument("-o", "--output", default="output.mp3", help="Output file")
    parser.add_argument("-d", "--duration", type=float, default=75.0, help="Duration in seconds")
    parser.add_argument("--bpm", type=float, default=150.0, help="Base BPM")
    parser.add_argument("--energy", type=float, default=0.8, help="Energy level 0-1")
    parser.add_argument("--distortion", type=int, default=4, help="Distortion stages")
    parser.add_argument("--amen-layers", type=int, default=2, help="Amen break layers")
    parser.add_argument("--bitcrush", type=int, default=16, help="Bit depth (1-16)")
    args = parser.parse_args()
    
    # Build custom layout
    sections = [
        Section("wish", 0, args.duration*0.1, energy=0.15, has_pad=True, pad_key="Cm7"),
        Section("ascension", args.duration*0.1, args.duration*0.2, energy=0.4, has_amen=True, amen_layers=1),
        Section("break1", args.duration*0.2, args.duration*0.32, energy=args.energy, has_amen=True, has_riddim=True, has_reese=True, distortion_stages=args.distortion, amen_layers=args.amen_layers),
        Section("void", args.duration*0.32, args.duration*0.4, energy=0.1, has_pad=True, pad_key="Cm7"),
        Section("break2", args.duration*0.4, args.duration*0.52, energy=args.energy, has_amen=True, has_riddim=True, has_reese=True, distortion_stages=args.distortion+1, amen_layers=args.amen_layers+1),
        Section("apotheosis", args.duration*0.52, args.duration*0.7, energy=1.0, has_amen=True, has_riddim=True, has_reese=True, distortion_stages=args.distortion+2, amen_layers=4, bitcrush=args.bitcrush),
        Section("dissolution", args.duration*0.7, args.duration*0.85, energy=0.3, bitcrush=max(1,args.bitcrush-4)),
        Section("free", args.duration*0.85, args.duration, energy=0.05, has_pad=True, pad_key="Em7"),
    ]
    
    engine = CognitohazardEngine(CognitohazardLayout(sections))
    print(f"φ = {PHI:.6f} | η* = 0.03 | Φ = 0.973")
    print(f"Rendering {args.duration}s at {args.bpm} BPM...")
    
    samples = engine.render(args.duration)
    
    wav_path = args.output.replace('.mp3', '.wav')
    render_to_file(samples, wav_path, args.output)
    print(f"Done: {args.output}")

if __name__ == "__main__":
    main()
