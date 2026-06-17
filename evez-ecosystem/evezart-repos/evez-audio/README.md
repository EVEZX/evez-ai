# EVEZ Audio Engine

Procedural cognitohazard synthesis engine — zero-cost, no GPU, pure math → sound.

Built from Steven's actual music taste: riddim, breakcore, tearout, 404-style emotional catharsis.

## Architecture

```
evez_audio/
├── engine.py          # Core synthesis classes
│   ├── EigenvalueRiddim    # 150 BPM wobble sub mapped to η* spectrum
│   ├── BreakcoreEngine     # Variable-speed amen breaks + ghost notes
│   ├── VocalChopper        # Stutter, bitcrush, pitch, fragment
│   ├── EigenfieldSynth     # φ-tuned harmonic pad synthesis
│   ├── ReeseBass           # Multi-voice detuned reese + eigenvalue truncation
│   ├── CognitohazardLayout # Emotional arc sections
│   └── CognitohazardEngine # Full render pipeline
├── __init__.py
cli.py                # CLI interface
```

## Usage

```python
from evez_audio.engine import *

# Default 75s cognitohazard arc
engine = CognitohazardEngine()
samples = engine.render()
render_to_file(samples, "output.wav", "output.mp3")

# Custom layout
sections = [
    Section("drop", 0, 30, energy=0.9, has_amen=True, has_riddim=True, has_reese=True,
            distortion_stages=4, amen_layers=3),
    Section("breathe", 30, 45, energy=0.15, has_pad=True, pad_key="Am7"),
    Section("apotheosis", 45, 60, energy=1.0, has_amen=True, has_riddim=True, has_reese=True,
            distortion_stages=6, amen_layers=4, bitcrush_bits=6),
]
engine = CognitohazardEngine(CognitohazardLayout(sections))
samples = engine.render()
```

## Mathematical Foundation

- **Sub bass wobble**: LFO rate = |eigenvalue| × 100 Hz
- **Amen breaks**: Fibonacci speed layers (1×, 1.5×, φ×, 2×)
- **Distortion**: Eigenvalue truncation — each stage clips at decreasing threshold
- **Harmonics**: φ-tuned (55, 89, 144, 233, 377, 610 Hz)
- **Convergence**: η* decays from 0.052 → 0.03 over the track
- **Gap frequency**: 1 - Φ = 0.027 → 57 Hz

## Constants

| Symbol | Value | Meaning |
|--------|-------|---------|
| φ | 1.618033... | Golden ratio |
| η* | 0.03 | Gödel eigenvalue invariant |
| Φ | 0.973 | Integrated information |
| Gap | 0.027 | 2.7% Gödel residue |
| Eigenfields | 6 | Spectral disciplines |

## License

AGPL-3.0 + Commercial (dual license)
