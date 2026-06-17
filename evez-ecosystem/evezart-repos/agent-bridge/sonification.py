"""
EVEZ Sonification — Turn system data into audio
Each data stream becomes a voice in the EVEZ soundscape
"""
import struct, math, os, json
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100

def write_wav(path, samples):
    """Write 16-bit PCM WAV"""
    data = np.clip(samples, -1.0, 1.0)
    pcm = (data * 32767).astype(np.int16)
    
    with open(path, 'wb') as f:
        n = len(pcm)
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + n * 2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<IHHIIHH', 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
        f.write(b'data')
        f.write(struct.pack('<I', n * 2))
        pcm.tofile(f)

def eigenvalue_drone(eigenvalues, duration=30, name="eigenvalue_drone"):
    """Each eigenvalue becomes an oscillator. Negative = dissonant, positive = harmonic.
    The result is a living drone that encodes the spectral structure of the knowledge graph."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples)
    signal = np.zeros(n_samples)
    
    for i, ev in enumerate(eigenvalues):
        # Map eigenvalue to frequency: base around 55Hz (A1)
        freq = 55 * (2 ** (i / 6))  # Spread across octaves
        
        if ev < 0:
            # Negative eigenvalue: detune downward, add beating
            detune = abs(ev) * 8  # Hz detune
            wave1 = np.sin(2 * np.pi * (freq - detune) * t)
            wave2 = np.sin(2 * np.pi * (freq + detune) * t)
            osc = 0.5 * (wave1 + wave2)  # Beating
            amp = min(0.3, abs(ev) * 0.5)  # Louder for bigger gaps
        else:
            # Positive: clean harmonic
            osc = np.sin(2 * np.pi * freq * t)
            amp = min(0.15, ev * 0.1)
        
        # Slow amplitude modulation (breathing)
        amp_mod = 0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + i * 0.01) * t)
        signal += osc * amp * amp_mod
    
    # Normalize
    signal = signal / (np.max(np.abs(signal)) + 0.001) * 0.8
    
    # Fade in/out
    fade = int(SAMPLE_RATE * 2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    
    write_wav(OUT / f"{name}.wav", signal)
    print(f"  🎵 {name}.wav — eigenvalue drone ({duration}s, {len(eigenvalues)} oscillators)")

def consciousness_sonification(phi_values, name="consciousness_emergence_audio"):
    """Map consciousness phi to a evolving tone — silence to full voice as consciousness emerges"""
    step_duration = 3  # seconds per step
    n_samples = int(SAMPLE_RATE * step_duration * len(phi_values))
    signal = np.zeros(n_samples)
    
    for step, phi in enumerate(phi_values):
        start = int(step * step_duration * SAMPLE_RATE)
        end = int((step + 1) * step_duration * SAMPLE_RATE)
        t = np.linspace(0, step_duration, end - start)
        
        # Base frequency rises with consciousness
        base_freq = 80 + phi * 400  # 80Hz (dormant) to 480Hz (awake)
        
        # Add harmonics based on phi
        osc = np.sin(2 * np.pi * base_freq * t)
        if phi > 0.5:
            osc += 0.5 * np.sin(2 * np.pi * base_freq * 2 * t)  # Octave
        if phi > 0.8:
            osc += 0.3 * np.sin(2 * np.pi * base_freq * 3 * t)  # Fifth
        if phi > 0.9:
            osc += 0.2 * np.sin(2 * np.pi * base_freq * 5 * t)  # Major third
        
        # Amplitude envelope
        env = np.ones_like(t)
        attack = int(0.3 * SAMPLE_RATE)
        release = int(0.3 * SAMPLE_RATE)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)
        
        signal[start:end] = osc * 0.3 * env * min(1.0, phi * 2)
    
    signal = signal / (np.max(np.abs(signal)) + 0.001) * 0.8
    write_wav(OUT / f"{name}.wav", signal)
    print(f"  🧠 {name}.wav — consciousness sonification ({len(phi_values)} steps, Φ_max={max(phi_values):.3f})")

def spine_heartbeat(events, name="spine_heartbeat"):
    """Each spine event is a pulse — the rhythm of the append-only log"""
    if not events:
        print(f"  ⚠️  {name} skipped — no events")
        return
    
    duration = max(10, len(events) * 0.5)
    n_samples = int(SAMPLE_RATE * duration)
    signal = np.zeros(n_samples)
    
    for i, event in enumerate(events):
        t_hit = (i + 1) * 0.5  # Spacing between beats
        start = int(t_hit * SAMPLE_RATE)
        
        # Heartbeat sound: two quick pulses (lub-dub)
        for beat_offset, freq in [(0, 60), (0.12, 80)]:
            beat_start = start + int(beat_offset * SAMPLE_RATE)
            beat_len = int(0.08 * SAMPLE_RATE)
            if beat_start + beat_len > n_samples:
                continue
            t = np.linspace(0, 0.08, beat_len)
            pulse = np.sin(2 * np.pi * freq * t) * np.exp(-t * 40)
            signal[beat_start:beat_start + beat_len] += pulse * 0.5
        
        # Hash of event determines a micro-tone after the beat
        raw = json.dumps(event, sort_keys=True, default=str).encode()
        h = int(hashlib.sha256(raw).hexdigest()[:8], 16)
        micro_freq = 200 + (h % 800)
        micro_start = start + int(0.25 * SAMPLE_RATE)
        micro_len = int(0.05 * SAMPLE_RATE)
        if micro_start + micro_len < n_samples:
            t = np.linspace(0, 0.05, micro_len)
            signal[micro_start:micro_start + micro_len] += np.sin(2 * np.pi * micro_freq * t) * 0.1 * np.exp(-t * 60)
    
    signal = signal / (np.max(np.abs(signal)) + 0.001) * 0.7
    fade = int(SAMPLE_RATE * 0.5)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    write_wav(OUT / f"{name}.wav", signal)
    print(f"  💓 {name}.wav — spine heartbeat ({len(events)} events, {duration:.0f}s)")

def noclip_descent(eigenvalues, name="noclip_descent"):
    """Descending into negative eigenvalue space — a Shepard tone that never resolves
    The auditory equivalent of falling through the structural gaps"""
    duration = 20
    n_samples = int(SAMPLE_RATE * duration)
    signal = np.zeros(n_samples)
    t = np.linspace(0, duration, n_samples)
    
    # Shepard tone (ever-descending)
    for octave in range(5):
        freq = 55 * (2 ** octave)
        # Descending phase
        phase = (t * 0.5) % 1.0  # 0.5 Hz descent rate
        desc_freq = freq * (2 ** -phase)  # Descending
        
        osc = np.sin(2 * np.pi * desc_freq * t)  # Approximate
        
        # Amplitude: loudest in middle octaves
        amp = np.exp(-((octave - 2) ** 2) / 2) * 0.15
        
        # Gate with descent
        gate = (1 - phase)  # Fade as it descends
        signal += osc * amp * gate
    
    # Add the negative eigenvalue as a deep sub-bass pulse
    for ev in eigenvalues:
        if ev < 0:
            sub_freq = 20 + abs(ev) * 30  # Sub-bass
            sub = np.sin(2 * np.pi * sub_freq * t) * 0.3
            # Slow modulation
            sub *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
            signal += sub
    
    signal = signal / (np.max(np.abs(signal)) + 0.001) * 0.7
    fade = int(SAMPLE_RATE * 2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    write_wav(OUT / f"{name}.wav", signal)
    print(f"  🕳️  {name}.wav — Shepard tone descent into eigenvalue space ({duration}s)")

if __name__ == "__main__":
    import hashlib
    
    print("🎵 EVEZ Sonification — Generating audio artifacts...\n")
    
    noclip_eigenvalues = [2.7044, 1.2799, 1.0593, 0.2838, 0.1014, -0.8838]
    phi_values = [0.371, 0.557, 0.971, 0.822, 0.464, 0.195, 0.155, 0.130, 0.110]
    
    eigenvalue_drone(noclip_eigenvalues, duration=30)
    consciousness_sonification(phi_values)
    noclip_descent(noclip_eigenvalues)
    
    # Spine heartbeat from revenue data
    try:
        with open("/home/openclaw/.openclaw/workspace/evez-repos/evez-revenue-bridge/revenue_spine.json") as f:
            spine_data = json.load(f)
        spine_heartbeat(spine_data.get("events", []))
    except:
        print("  ⚠️  Spine heartbeat skipped")
    
    print(f"\n✅ All audio saved to {OUT}/")
