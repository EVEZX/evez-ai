# Installation Guide

## Requirements
- Python 3.8+
- Optional: `ffmpeg` (for MP4 animation export)

## Pip dependencies
```bash
pip install numpy pillow scipy
```

## OpenClaw / ClawHub (recommended)
```bash
clawhub install evez-os
evez play --seed 42 --steps 14
```

## Manual
```bash
git clone https://github.com/EvezArt/evez-os.git
cd evez-os
pip install numpy pillow scipy
python3 tools/evez.py play --seed 42 --steps 14
```

## Verify install
```bash
python3 tools/evez.py lint
# Expected: "Lint: N OK, 0 violations ✅"
```

## What you get after first run
- `spine/spine.jsonl` — append-only cognition log
- `manifest.json` — tamper-evident session manifest  
- `cognition_map.png` — visual lobby transition map (run visualize-thought)

## Commercial License
Remove AGPL obligations: https://rubikspubes.gumroad.com
