"""
EVEZ Breakcore Engine — 404/Breakcore/Skrillex/Dysym/Aloboi style
Continuous generative breakcore music with live remixing.
"""
import os, sys, struct, math, random, time, io, wave, threading, queue
from collections import deque
import numpy as np
import soundfile as sf

SR = 44100
BPM = 174
BEAT_SAMPLES = int(SR * 60 / BPM)
BAR_SAMPLES = BEAT_SAMPLES * 4
CHUNK = 4096

class AmenBreak:
    def __init__(self, sr=SR):
        self.sr = sr

    def kick(self, length=0.15, pitch_start=150, pitch_end=40, decay=8):
        t = np.linspace(0, length, int(self.sr * length), False)
        pitch = np.linspace(pitch_start, pitch_end, len(t))
        phase = 2 * np.pi * np.cumsum(pitch) / self.sr
        sig = np.sin(phase) * np.exp(-decay * t)
        sub = np.sin(2 * np.pi * 50 * t) * np.exp(decay * 0.5 * t) * 0.3
        combined = sig + sub
        return combined / (np.max(np.abs(combined)) + 1e-6)

    def snare(self, length=0.2, tone=200, noise_mix=0.6, decay=12):
        t = np.linspace(0, length, int(self.sr * length), False)
        tone_sig = np.sin(2 * np.pi * tone * t) * np.exp(-decay * t)
        noise = np.random.randn(len(t)) * np.exp(-decay * 1.5 * t)
        sig = (1 - noise_mix) * tone_sig + noise_mix * noise
        return sig / (np.max(np.abs(sig)) + 1e-6)

    def hat(self, length=0.05, freq=8000, decay=30, open_prob=0.3):
        if random.random() < open_prob:
            length = 0.2
            decay = 12
        t = np.linspace(0, length, int(self.sr * length), False)
        noise = np.random.randn(len(t))
        carrier = np.sin(2 * np.pi * freq * t + 3 * np.sin(2 * np.pi * 3000 * t))
        sig = noise * carrier * np.exp(-decay * t)
        return sig / (np.max(np.abs(sig)) + 1e-6)

    def generate_pattern(self, pattern_type="amen"):
        bar = np.zeros(BAR_SAMPLES)
        sixteenth = BAR_SAMPLES // 16
        kicks, snares, hats = [], [], []

        if pattern_type == "amen":
            kicks = [0, 6, 10]; snares = [4, 12]; hats = list(range(16))
        elif pattern_type == "amen_var1":
            kicks = [0, 3, 6, 11]; snares = [4, 8, 12, 14]; hats = list(range(16))
        elif pattern_type == "amen_var2":
            kicks = [0, 5, 10, 13]; snares = [4, 8, 12]; hats = [i for i in range(16) if i % 2 == 0]
        elif pattern_type == "heavy":
            kicks = [0, 2, 5, 7, 10, 12, 14]; snares = [4, 8, 12, 15]; hats = list(range(16))
        elif pattern_type == "half":
            kicks = [0, 8]; snares = [4, 12]; hats = [i for i in range(16) if i % 2 == 0]
        elif pattern_type == "breakcore":
            kicks = sorted(random.sample(range(16), random.randint(5, 9)))
            snares = sorted(random.sample([i for i in range(16) if i not in kicks], random.randint(2, 4)))
            hats = [i for i in range(16) if random.random() > 0.3]
        else:
            kicks = [0, 6, 10]; snares = [4, 12]; hats = list(range(16))

        kick_s = self.kick()
        snare_s = self.snare()
        for k in kicks:
            pos = k * sixteenth; end = min(pos + len(kick_s), BAR_SAMPLES)
            bar[pos:end] += kick_s[:end-pos]
        for s in snares:
            pos = s * sixteenth; end = min(pos + len(snare_s), BAR_SAMPLES)
            bar[pos:end] += snare_s[:end-pos]
        for h in hats:
            pos = h * sixteenth; h_s = self.hat(); end = min(pos + len(h_s), BAR_SAMPLES)
            bar[pos:end] += h_s[:end-pos] * 0.3

        mx = np.max(np.abs(bar))
        if mx > 0: bar = bar / mx * 0.8
        return bar

    def generate_fill(self, intensity=1.0):
        bar = np.zeros(BAR_SAMPLES)
        sixteenth = BAR_SAMPLES // 16
        for i in range(16):
            if random.random() < 0.7 * intensity:
                pos = i * sixteenth
                if random.random() < 0.4:
                    s = self.snare(tone=random.randint(150, 300))
                else:
                    s = self.kick(pitch_start=random.randint(100, 200))
                end = min(pos + len(s), BAR_SAMPLES)
                bar[pos:end] += s[:end-pos]
            for j in range(2):
                if random.random() < 0.5 * intensity:
                    pos = i * sixteenth + j * sixteenth // 2
                    h = self.hat(length=0.03); end = min(pos + len(h), BAR_SAMPLES)
                    if pos < BAR_SAMPLES: bar[pos:end] += h[:end-pos] * 0.2
        mx = np.max(np.abs(bar))
        if mx > 0: bar = bar / mx * 0.9
        return bar

class BassEngine:
    def __init__(self, sr=SR):
        self.sr = sr

    def _lowpass(self, sig, cutoff):
        rc = 1.0 / (2 * np.pi * cutoff); dt = 1.0 / self.sr; alpha = dt / (rc + dt)
        out = np.zeros_like(sig); out[0] = sig[0] * alpha
        for i in range(1, len(sig)): out[i] = out[i-1] + alpha * (sig[i] - out[i-1])
        return out

    def _lowpass_sweep(self, sig, cutoff_arr):
        out = np.zeros_like(sig); out[0] = sig[0] * 0.001
        for i in range(1, len(sig)):
            rc = 1.0 / (2 * np.pi * max(cutoff_arr[i], 20)); dt = 1.0 / self.sr; alpha = dt / (rc + dt)
            out[i] = out[i-1] + alpha * (sig[i] - out[i-1])
        return out

    def reese(self, freq=55, length=2.0, detune=1.5, distortion=0.8):
        t = np.linspace(0, length, int(self.sr * length), False)
        saw1 = 2 * (freq * t % 1) - 1; saw2 = 2 * ((freq + detune * (1 + 0.01 * np.sin(2*np.pi*0.5*t))) * t % 1) - 1
        sig = 0.5 * (saw1 + saw2)
        sig = self._lowpass(sig, freq * 6)
        sig = np.tanh(sig * (1 + distortion * 4)) / np.tanh(1 + distortion * 4)
        env = np.ones_like(t); attack = int(0.01 * self.sr); release = int(0.1 * self.sr)
        env[:attack] = np.linspace(0, 1, attack); env[-release:] = np.linspace(1, 0, release)
        return (sig * env) / (np.max(np.abs(sig * env)) + 1e-6)

    def sub808(self, freq=40, length=1.0, saturation=2.0):
        t = np.linspace(0, length, int(self.sr * length), False)
        sig = np.sin(2 * np.pi * freq * t); sig = np.tanh(sig * saturation)
        return (sig * np.exp(-3 * t) * 0.8) / (np.max(np.abs(sig * np.exp(-3 * t) * 0.8)) + 1e-6)

    def neuro(self, freq=55, length=2.0, lfo_rate=3.0, lfo_depth=0.5):
        t = np.linspace(0, length, int(self.sr * length), False)
        saw = 2 * (freq * t % 1) - 1
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * lfo_rate * t)
        cutoff = freq * (3 + lfo * lfo_depth * 20)
        sig = self._lowpass_sweep(saw, cutoff); sig = np.tanh(sig * 3)
        return sig / (np.max(np.abs(sig)) + 1e-6)

class FXChain:
    @staticmethod
    def bitcrusher(sig, bits=8, downsample=4):
        steps = 2 ** bits; crushed = np.round(sig * steps / 2) / (steps / 2)
        if downsample > 1:
            hold = crushed[::downsample]; idx = (np.arange(len(crushed)) // downsample).astype(int)
            crushed = hold[np.clip(idx, 0, len(hold) - 1)]
        return crushed

    @staticmethod
    def distort(sig, drive=5.0, mix=0.5):
        return (1 - mix) * sig + mix * np.tanh(sig * drive)

    @staticmethod
    def reverb(sig, decay=0.3, n_reflections=8, sr=SR):
        out = sig.copy()
        for i in range(n_reflections):
            delay = int(sr * (0.02 + random.random() * 0.08))
            delayed = np.zeros_like(sig)
            if delay < len(sig): delayed[delay:] = sig[:-delay] * (decay ** (i + 1))
            out += delayed / n_reflections
        mx = np.max(np.abs(out))
        if mx > 0: out = out / mx * np.max(np.abs(sig))
        return out

    @staticmethod
    def delay_fx(sig, time_beat=0.25, feedback=0.4, sr=SR):
        delay_samples = int(time_beat * 60 / BPM * sr); out = sig.copy()
        for i in range(4):
            shifted = delay_samples * (i + 1)
            if shifted < len(sig): out[shifted:] += sig[:-shifted] * (feedback ** (i + 1))
        mx = np.max(np.abs(out))
        if mx > 0: out = out / mx * np.max(np.abs(sig))
        return out

    @staticmethod
    def sidechain(sig, kick_positions, bar_len, amount=0.7, release=0.1, sr=SR):
        env = np.ones(len(sig)); release_samples = int(release * sr)
        for pos in kick_positions:
            pos_samples = int(pos * bar_len)
            for j in range(min(release_samples, len(env) - pos_samples)):
                t_ratio = j / release_samples
                env[pos_samples + j] = min(env[pos_samples + j], 1 - amount * (1 - t_ratio))
        return sig * env

class RemixLayer:
    @staticmethod
    def stutter(bar, count=4, sixteenth_idx=None):
        sixteenth = len(bar) // 16
        if sixteenth_idx is None: sixteenth_idx = random.randint(0, 15)
        start = sixteenth_idx * sixteenth; slice_ = bar[start:start+sixteenth].copy()
        out = bar.copy()
        for i in range(count):
            pos = start + i * sixteenth // count; end = min(pos + sixteenth // count, len(out))
            chunk = min(sixteenth // count, len(slice_))
            if pos < len(out): out[pos:pos+chunk] = slice_[:chunk]
        return out

    @staticmethod
    def reverse_slice(bar, sixteenth_idx=None):
        sixteenth = len(bar) // 16
        if sixteenth_idx is None: sixteenth_idx = random.randint(0, 15)
        start = sixteenth_idx * sixteenth; end = min(start + sixteenth, len(bar))
        out = bar.copy(); out[start:end] = bar[start:end][::-1]
        return out

    @staticmethod
    def random_mutation(bar, intensity=0.3):
        out = bar.copy(); n = int(intensity * 5) + 1
        for _ in range(n):
            c = random.random()
            if c < 0.3: out = RemixLayer.stutter(out, count=random.choice([2, 4, 8]))
            elif c < 0.5: out = RemixLayer.reverse_slice(out)
            elif c < 0.7:
                sixteenth = len(out) // 16; idx = random.randint(0, 15); start = idx * sixteenth
                end = min(start + sixteenth, len(out))
                out[start:end] = FXChain.bitcrusher(out[start:end], bits=random.choice([4, 6, 8]))
        return out

class Arranger:
    SECTIONS = ["buildup", "drop1", "breakdown", "drop2", "switch", "drop3", "outro", "intro"]
    def __init__(self):
        self.section_idx = 0; self.bars_in_section = 0; self.section_length = 4
        self.intensity = 0.0; self.current_pattern = "amen"

    def next_bar(self):
        self.bars_in_section += 1
        section = self.SECTIONS[self.section_idx % len(self.SECTIONS)]
        if self.bars_in_section >= self.section_length:
            self.bars_in_section = 0; self.section_idx += 1
            new_section = self.SECTIONS[self.section_idx % len(self.SECTIONS)]
            if "drop" in new_section:
                self.intensity = random.uniform(0.7, 1.0)
                self.current_pattern = random.choice(["breakcore", "heavy", "amen_var1", "amen_var2"])
                self.section_length = random.choice([4, 8, 16])
            elif new_section == "breakdown":
                self.intensity = random.uniform(0.2, 0.4); self.current_pattern = "half"; self.section_length = 4
            elif new_section == "buildup":
                self.intensity = random.uniform(0.4, 0.7); self.current_pattern = "amen"; self.section_length = 4
            elif new_section == "switch":
                self.intensity = random.uniform(0.6, 0.9)
                self.current_pattern = random.choice(["amen_var1", "amen_var2", "heavy", "breakcore"])
                self.section_length = random.choice([2, 4])
        return section, self.intensity, self.current_pattern

    @property
    def should_fill(self):
        return self.bars_in_section == self.section_length - 1 and self.intensity > 0.5

def dark_pad(freq=55, length=32.0, sr=SR):
    t = np.linspace(0, length, int(sr * length), False)
    sig = np.zeros_like(t)
    for i in range(5):
        f = freq * (1 + (i - 2) * 0.01)
        sig += np.sin(2 * np.pi * f * t) * 0.2 + np.sin(2 * np.pi * f * 2.01 * t) * 0.1
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    return sig / (np.max(np.abs(sig)) + 1e-6) * 0.15 * lfo

class BreakcoreEngine:
    def __init__(self):
        self.amen = AmenBreak(); self.bass = BassEngine(); self.fx = FXChain()
        self.arranger = Arranger(); self.remix = RemixLayer()
        self.running = False; self.bar_count = 0; self.bpm = BPM; self.current_section = "intro"
        self.bass_notes = {
            "low": self.bass.reese(40, 2.0, 2.0, 1.0), "mid": self.bass.reese(55, 2.0, 1.5, 0.8),
            "high": self.bass.neuro(65, 2.0, 4.0, 0.6), "sub": self.bass.sub808(40, 2.0, 3.0),
        }
        self.pad = dark_pad(55, 32.0); self.pad_pos = 0; self._bar_buffer = np.array([], dtype=np.float32)

    def generate_bar(self):
        section, intensity, pattern = self.arranger.next_bar()
        self.current_section = section
        if self.arranger.should_fill and random.random() < 0.7:
            breaks = self.amen.generate_fill(intensity)
        else:
            breaks = self.amen.generate_pattern(pattern)
        if intensity > 0.7 and random.random() < 0.4: breaks = RemixLayer.random_mutation(breaks, intensity)
        if intensity > 0.8 and random.random() < 0.3: breaks = self.fx.bitcrusher(breaks, bits=random.choice([6, 8, 10]))

        bass_key = "sub" if "drop" in section else "high" if section == "breakdown" else random.choice(["mid", "high"])
        bass_audio = self.bass_notes[bass_key]
        if len(bass_audio) < BAR_SAMPLES:
            bass_audio = np.tile(bass_audio, (BAR_SAMPLES // len(bass_audio)) + 1)[:BAR_SAMPLES]
        else:
            bass_audio = bass_audio[:BAR_SAMPLES]

        kick_positions = [0, 0.375]
        bass_audio = self.fx.sidechain(bass_audio, kick_positions, BAR_SAMPLES, amount=0.6, release=0.15)

        pad_chunk = self.pad[self.pad_pos:self.pad_pos + BAR_SAMPLES]
        self.pad_pos = (self.pad_pos + BAR_SAMPLES) % len(self.pad)
        if len(pad_chunk) < BAR_SAMPLES: pad_chunk = np.pad(pad_chunk, (0, BAR_SAMPLES - len(pad_chunk)))

        length = max(len(breaks), len(bass_audio))
        mix = np.zeros(length)
        mix[:len(breaks)] += breaks * (0.6 + intensity * 0.3)
        mix[:len(bass_audio)] += bass_audio * (0.3 + intensity * 0.3)
        mix[:len(pad_chunk)] += pad_chunk * (0.1 + (0.15 if section == "breakdown" else 0))

        mix = self.fx.sidechain(mix, kick_positions, len(mix), amount=0.5, release=0.08)
        # Limiter
        for i in range(len(mix)):
            if abs(mix[i]) > 0.92: mix[i] = 0.92 * np.sign(mix[i])
        mx = np.max(np.abs(mix))
        if mx > 0: mix = mix / mx
        self.bar_count += 1
        return mix

    def to_wav_bytes(self, audio_float, sr=SR):
        buf = io.BytesIO()
        sf.write(buf, audio_float, sr, format='WAV', subtype='PCM_16')
        buf.seek(0)
        return buf.read()

    def generate_bar_wav(self):
        return self.to_wav_bytes(self.generate_bar())

# FastAPI
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

app = FastAPI(title="EVEZ Breakcore Engine", version="1.0.0")
engine = BreakcoreEngine()

@app.get("/")
async def index():
    return HTMLResponse("""<html><head><title>⚡ 404 Breakcore</title>
<style>body{background:#000;color:#ff0066;font-family:monospace;text-align:center;padding:50px;}
a{color:#00ffc8;font-size:24px;}</style></head><body>
<h1>⚡ 404 BREAKCORE ⚡</h1><p>Continuous generative breakcore • 174 BPM</p>
<p>Skrillex • Dysym • Aloboi • 404 vibes</p><br>
<a href="/stream">🎧 LISTEN LIVE (WAV)</a><br><br>
<a href="/bar.wav">🎶 Single Bar</a><br><br>
<a href="/snapshot">📸 Snapshot</a><br><br>
<p style="color:#666">Bar: <span id="bar">0</span> | Section: <span id="sec">intro</span></p>
<script>setInterval(async()=>{try{const r=await fetch('/stats');const d=await r.json();
document.getElementById('bar').textContent=d.bar;document.getElementById('sec').textContent=d.section;}catch{}},2000)</script>
</body></html>""")

@app.get("/stream")
async def stream_wav():
    def gen():
        while True:
            bar = engine.generate_bar()
            yield engine.to_wav_bytes(bar)
    return StreamingResponse(gen(), media_type="audio/wav")

@app.get("/bar.wav")
async def single_bar():
    bar = engine.generate_bar()
    return Response(content=engine.to_wav_bytes(bar), media_type="audio/wav")

@app.get("/snapshot")
async def snapshot():
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1920, 1080), (10, 0, 20))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaSans-Bold.ttf", 36)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
    except:
        font = font_sm = ImageFont.load_default()
    draw.text((50, 50), "⚡ 404 BREAKCORE ⚡", fill=(255, 0, 100), font=font)
    draw.text((50, 120), f"BAR: {engine.bar_count}  SECTION: {engine.current_section}  BPM: 174", fill=(0, 255, 200), font=font_sm)
    bar = engine.generate_bar()
    step = max(1, len(bar) // 960); samples = bar[::step][:960]; y_center = 540
    for i, s in enumerate(samples):
        x = 50 + i * 2; y = y_center - int(s * 300)
        draw.line([(x, y_center), (x, y)], fill=(255, 0, 100), width=1)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg")

@app.get("/stats")
async def stats():
    return {"bar": engine.bar_count, "section": engine.current_section, "bpm": engine.bpm, "running": engine.running}

if __name__ == "__main__":
    engine.running = True
    port = int(os.getenv("BREAKCORE_PORT", "8896"))
    print(f"⚡ EVEZ 404 Breakcore Engine starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
