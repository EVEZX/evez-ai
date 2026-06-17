#!/usr/bin/env python3
"""
EVEZ Voice+Audio Pipeline
1. Generate beat with CognitohazardEngine
2. Clone voice via Chatterbox HF Spaces
3. Mix vocals into beat at 404-style positions
4. Output final track
"""
import sys
import os
import subprocess

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evez_audio.engine import *

def generate_track(sections=None, output_path="output.mp3", vocal_clips=None):
    """
    Generate a full cognitohazard track with optional vocal integration.
    
    vocal_clips: list of (path, delay_ms, tempo_mult, volume) tuples
    """
    if sections is None:
        sections = CognitohazardLayout.DEFAULT_ARC
    
    # Render beat
    engine = CognitohazardEngine(CognitohazardLayout(sections))
    samples = engine.render()
    
    wav_path = output_path.replace('.mp3', '.wav')
    render_to_wav(samples, wav_path)
    
    # Convert to mp3
    subprocess.run(['ffmpeg', '-y', '-i', wav_path, '-c:a', 'libmp3lame',
                     '-b:a', '256k', output_path], 
                    capture_output=True, check=True)
    
    # Mix vocals if provided
    if vocal_clips:
        inputs = [['-i', output_path]]
        filter_parts = ["[0:a]aresample=44100,volume=0.55[beat]"]
        
        for idx, (clip_path, delay_ms, tempo, vol) in enumerate(vocal_clips):
            label = f"vocal{idx}"
            inputs.append(['-i', clip_path])
            filter_parts.append(
                f"[{idx+1}:a]aresample=44100,atempo={tempo},volume={vol},highpass=f=180[{label}_raw]"
            )
            filter_parts.append(f"[{label}_raw]adelay={delay_ms}|{delay_ms}[{label}]")
        
        # Build mix string
        mix_inputs = "[beat]" + "".join(f"[{f'vocal{i}'}]" for i in range(len(vocal_clips)))
        n_inputs = 1 + len(vocal_clips)
        filter_parts.append(f"{mix_inputs}amix=inputs={n_inputs}:duration=longest:dropout_transition=0")
        
        filter_complex = ";".join(filter_parts)
        
        final_path = output_path.replace('.mp3', '-voiced.mp3')
        cmd = ['ffmpeg', '-y']
        for group in inputs:
            cmd.extend(group)
        cmd.extend([
            '-filter_complex', filter_complex,
            '-c:a', 'libmp3lame', '-b:a', '256k', final_path
        ])
        
        subprocess.run(cmd, capture_output=True, check=True)
        return final_path
    
    return output_path

if __name__ == "__main__":
    path = generate_track(
        output_path="/tmp/pipeline-test.mp3",
        vocal_clips=[
            ("/home/openclaw/.openclaw/workspace/media/cog-hazard-chops-1.mp3", 18000, 1.3, 1.6),
            ("/home/openclaw/.openclaw/workspace/media/cog-hazard-chops-2.mp3", 34000, 1.2, 1.6),
        ]
    )
    print(f"Output: {path}")
