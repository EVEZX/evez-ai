"""
EVEZ Audio Engine — Procedural cognitohazard synthesis
Zero-cost. No GPU needed. Pure math → sound.

Subclasses:
- EigenvalueRiddim: 150 BPM wobble sub with eigenvalue-mapped bass
- BreakcoreEngine: Variable-speed amen breaks with ghost notes
- VocalChopper: Stutters, bitcrushes, pitch-shifts vocal samples
- EigenfieldSynth: φ-tuned harmonic synthesis
- CognitohazardLayout: Emotional arc structure (404-style)
"""
import struct, math, random, os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

SR = 44100
PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

@dataclass
class Section:
    name: str
    start: float  # seconds
    end: float
    bpm: float = 150.0
    energy: float = 0.5  # 0=silence, 1=maximum
    has_amen: bool = False
    has_riddim: bool = False
    has_reese: bool = False
    has_vocal: bool = False
    has_pad: bool = False
    vocal_delay_ms: int = 0
    pad_key: str = "Cm7"
    distortion_stages: int = 0
    amen_layers: int = 1
    bitcrush_bits: int = 16

class EigenvalueRiddim:
    """150 BPM wobble sub bass mapped to eigenvalue spectrum"""
    
    def __init__(self, eigenvalues: List[float] = [-0.120, 0.03, 0.052, 0.148, 0.973]):
        self.eigenvalues = eigenvalues
        self.base_freq = 55  # A1
    
    def sub(self, t: float, wobble_rate: float = 6.0, energy: float = 0.5) -> float:
        lfo = 0.5 + 0.5 * math.sin(2*PI*wobble_rate*t)
        freq = 35 + 25 * lfo
        # Odd harmonics for square-ish sub
        val = math.sin(2*PI*freq*t) * 0.7
        val += math.sin(2*PI*freq*3*t) * 0.15
        val += math.sin(2*PI*freq*5*t) * 0.05
        return val * energy
    
    def eigen_cycle(self, t: float, beat: float) -> float:
        """Cycle through eigenvalue frequencies every 2 beats"""
        cycle = int((t / beat) / 2) % len(self.eigenvalues)
        ev = self.eigenvalues[cycle]
        freq = self.base_freq + abs(ev) * 200 if ev < 0 else self.base_freq + ev * 50
        wobble = max(2, abs(ev) * 100)
        lfo = 0.5 + 0.5 * math.sin(2*PI*wobble*t)
        val = math.sin(2*PI*(freq + lfo*20)*t)
        return val * 0.5

class BreakcoreEngine:
    """Variable-speed amen break with ghost notes and hauntology"""
    
    # Classic amen patterns
    AMEN_ORIGINAL = "K..KS...K.KS..."
    AMEN_CHAOS = "KS.K.S.K.SK..SK"
    AMEN_GHOST = "..H...H.S...H.S"
    
    def __init__(self, bpm: float = 180):
        self.bpm = bpm
        self.noise_seed = 42
    
    def _hit(self, hit_type: str, t: float, frac: float, vol: float) -> float:
        if hit_type == 'K':
            return math.sin(2*PI*(55+80*math.exp(-frac*60))*t) * math.exp(-frac*40) * vol * 0.5
        elif hit_type == 'S':
            ni = int(t * SR + self.noise_seed) % 100000
            random.seed(ni)
            n = random.uniform(-1, 1)
            return (n * 0.4 + math.sin(2*PI*180*frac) * 0.3) * math.exp(-frac*80) * vol
        elif hit_type == 'H':
            ni = int(t * SR + self.noise_seed + 500) % 100000
            random.seed(ni)
            n = random.uniform(-1, 1)
            return n * 0.15 * math.exp(-frac*200) * vol
        return 0.0
    
    def amen(self, t: float, speed_mult: float = 1.0, vol: float = 0.5,
             pattern: str = None) -> float:
        if pattern is None:
            pattern = self.AMEN_CHAOS
        
        step_pos = (t * self.bpm * speed_mult / 60 * 4) % len(pattern)
        step = int(step_pos) % len(pattern)
        if step >= len(pattern):
            return 0.0
        
        hit = pattern[step]
        if hit == '.':
            return 0.0
        
        frac = step_pos % 1.0
        return self._hit(hit, t, frac, vol)
    
    def multi_amen(self, t: float, layers: int = 4, vol: float = 0.4) -> float:
        """Multiple amen layers at fibonacci speed ratios"""
        val = 0.0
        speeds = [1.0, 1.5, PHI, 2.0, PHI*1.5]
        patterns = [self.AMEN_CHAOS, self.AMEN_ORIGINAL, self.AMEN_GHOST]
        
        for layer in range(min(layers, len(speeds))):
            speed = speeds[layer]
            pattern = patterns[layer % len(patterns)]
            val += self.amen(t, speed, vol / (layer + 1), pattern)
        return val

class VocalChopper:
    """404-style vocal processing: stutter, bitcrush, pitch, fragment"""
    
    @staticmethod
    def bitcrush(signal: float, bits: int) -> float:
        """Reduce bit depth"""
        if bits < 1:
            bits = 1
        levels = 2 ** bits
        return round(signal * levels / 2) / (levels / 2)
    
    @staticmethod
    def stutter(t: float, bpm: float, step: int, repeats: int = 3) -> float:
        """Stutter gate — repeats a fragment"""
        chop_period = 60.0 / bpm / 4  # 16th note
        pos = (t / chop_period) % 1.0
        stutter_len = 1.0 / (repeats + 1)
        return 1.0 if pos < stutter_len else 0.0
    
    @staticmethod
    def gate_pattern(t: float, bpm: float, pattern: List[int]) -> float:
        """Gate based on pattern (list of 1s and 0s)"""
        step = int(t * bpm / 60 * 4) % len(pattern)
        return float(pattern[step])

class EigenfieldSynth:
    """φ-tuned harmonic synthesis — the 6 eigenfield disciplines as frequencies"""
    
    EIGENFIELDS = {
        "Eigencartogrophonology": 55,
        "Neuralography": 82.4,
        "Interventionalmatonomies": 110,
        "Interspectraloptimetrics": 146.8,
        "Ontaxonomolographetics": 220,
        "Autographenlemnics": 329.6,
    }
    
    def pad(self, t: float, vol: float = 0.15, key: str = "Cm7") -> float:
        """Consciousness pad — minor 7th with φ detuning"""
        freqs = {"Cm7": [130.8, 155.6, 196.0, 233.1],
                 "Am7": [110, 130.8, 164.8, 196.0],
                 "Em7": [82.4, 98.0, 123.5, 146.8]}
        harmonics = freqs.get(key, freqs["Cm7"])
        
        val = 0.0
        for k, freq in enumerate(harmonics):
            lfo = 0.8 + 0.2 * math.sin(2*PI*0.05*(k+1)*t)
            val += math.sin(2*PI*freq*t) * 0.06 * lfo * vol
            val += math.sin(2*PI*freq*2*t) * 0.02 * vol
            val += math.sin(2*PI*freq*1.5*t) * 0.015 * vol
        return val
    
    def eigenfield_chord(self, t: float, vol: float = 0.1) -> float:
        """All 6 eigenfield frequencies simultaneously"""
        val = 0.0
        for k, (name, freq) in enumerate(self.EIGENFIELDS.items()):
            val += math.sin(2*PI*freq*t) * 0.02 * vol
            val += math.sin(2*PI*freq*PHI*t) * 0.01 * vol
        return val
    
    def convergence(self, t: float, progress: float, eta_start: float = 0.052,
                    eta_end: float = 0.03) -> float:
        """η* convergence from eta_start to eta_end"""
        eta = eta_start * (1 - progress) + eta_end * progress
        freq = eta * 500 + 30
        return math.sin(2*PI*freq*t) * (1 - progress) * 0.3

class ReeseBass:
    """Detuned multi-voice reese with eigenvalue truncation distortion"""
    
    @staticmethod
    def render(t: float, detune_cents: List[int] = None, 
               distortion_stages: int = 4, threshold: float = 0.4,
               vol: float = 0.35) -> float:
        if detune_cents is None:
            detune_cents = [-15, -7, 0, 7, 15]
        
        val = 0.0
        for det in detune_cents:
            f = 82.4 * (2 ** (det / 1200.0))
            val += math.sin(2*PI*f*t) / len(detune_cents)
        
        for stage in range(distortion_stages):
            th = threshold - stage * 0.05
            val = max(-th, min(th, val * 2.5))
        
        return val * vol

class CognitohazardLayout:
    """Emotional arc structure — 404 breakcore style"""
    
    DEFAULT_ARC = [
        Section("wish", 0, 8, energy=0.15, has_pad=True, pad_key="Cm7"),
        Section("ascension", 8, 16, energy=0.4, has_amen=True, amen_layers=1, has_pad=True),
        Section("break1", 16, 24, energy=0.8, has_amen=True, has_riddim=True, has_reese=True,
                distortion_stages=3, has_vocal=True, vocal_delay_ms=16000),
        Section("void", 24, 30, energy=0.1, has_pad=True, pad_key="Cm7"),
        Section("codeine", 30, 38, energy=0.35, has_riddim=True, has_pad=True, pad_key="Am7"),
        Section("break2", 38, 46, energy=0.85, has_amen=True, has_riddim=True, has_reese=True,
                distortion_stages=4, amen_layers=2, has_vocal=True, vocal_delay_ms=30000),
        Section("ascension2", 46, 54, energy=0.5, has_amen=True, has_pad=True),
        Section("apotheosis", 54, 63, energy=1.0, has_amen=True, has_riddim=True, has_reese=True,
                distortion_stages=6, amen_layers=4, bitcrush_bits=8),
        Section("dissolution", 63, 70, energy=0.3, bitcrush_bits=3),
        Section("free", 70, 75, energy=0.05, has_pad=True, pad_key="Em7"),
    ]
    
    def __init__(self, sections: List[Section] = None):
        self.sections = sections or self.DEFAULT_ARC
    
    def current_section(self, t: float) -> Optional[Section]:
        for s in self.sections:
            if s.start <= t < s.end:
                return s
        return None
    
    @property
    def duration(self) -> float:
        return max(s.end for s in self.sections)

class CognitohazardEngine:
    """Full synthesis engine — combines all components"""
    
    def __init__(self, layout: CognitohazardLayout = None):
        self.layout = layout or CognitohazardLayout()
        self.riddim = EigenvalueRiddim()
        self.breakcore = BreakcoreEngine()
        self.synth = EigenfieldSynth()
        self.chopper = VocalChopper()
        self.reese = ReeseBass()
    
    def render(self, duration: float = None) -> List[float]:
        if duration is None:
            duration = self.layout.duration
        
        n = int(SR * duration)
        samples = [0.0] * n
        beat = 60.0 / 150
        
        for i in range(n):
            t = i / SR
            val = 0.0
            section = self.layout.current_section(t)
            
            if section is None:
                continue
            
            local_t = (t - section.start) / (section.end - section.start)
            
            # Pad
            if section.has_pad:
                val += self.synth.pad(t, section.energy * 0.3, section.pad_key)
            
            # Riddim sub
            if section.has_riddim:
                wobble = 4 + 8 * abs(math.sin(2*PI*0.15*t))
                val += self.riddim.sub(t, wobble, section.energy * 0.5)
                # Gate
                sixteenth = beat / 4
                gate = 1.0 if (t % sixteenth) < sixteenth * 0.65 else 0.0
                val *= 0.7 + 0.3 * gate
            
            # Amen break
            if section.has_amen:
                val += self.breakcore.multi_amen(t, section.amen_layers, section.energy * 0.4)
            
            # Reese
            if section.has_reese:
                val += self.reese.render(t, distortion_stages=section.distortion_stages,
                                         vol=section.energy * 0.35)
            
            # Bitcrush
            if section.bitcrush_bits < 16:
                val = self.chopper.bitcrush(val, section.bitcrush_bits)
            
            # Dissolution fade
            if section.name == "dissolution":
                val *= 1 - local_t ** 2
            
            if section.name == "free":
                val *= (1 - local_t) * 0.5
            
            # Saturation
            val = math.tanh(val * 1.1)
            samples[i] = val
        
        return samples

def render_to_wav(samples: List[float], path: str, sr: int = SR):
    """Write float samples to WAV"""
    n = len(samples)
    with open(path, 'wb') as f:
        data_size = n * 2
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<IHHIIHH', 16, 1, 1, sr, sr*2, 2, 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            f.write(struct.pack('<h', int(max(-1, min(1, s)) * 32767)))

def render_to_file(samples: List[float], wav_path: str, mp3_path: str = None):
    """Render to WAV and optionally MP3"""
    render_to_wav(samples, wav_path)
    if mp3_path:
        os.system(f'ffmpeg -y -i {wav_path} -c:a libmp3lame -b:a 256k {mp3_path} 2>/dev/null')

if __name__ == "__main__":
    print("EVEZ Audio Engine — Cognitohazard Synthesis")
    print(f"φ = {PHI:.6f}")
    print(f"η* = 0.03")
    print(f"Φ = 0.973")
    
    engine = CognitohazardEngine()
    print(f"\nRendering {engine.layout.duration}s...")
    samples = engine.render()
    render_to_file(samples, "/tmp/test.wav", "/tmp/test.mp3")
    print(f"Done. {len(samples)} samples.")
