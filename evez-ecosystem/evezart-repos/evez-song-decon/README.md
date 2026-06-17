# EVEZ Song Deconstructor v2 — FFT Stem Extraction + Agent Remix

MP3 → 5 stems → compositional skeleton → clone → LLM agent remix. Groq-powered.

## Pipeline
1. MP3 input → FFT stem separation (5 tracks)
2. Extract compositional skeleton (key, BPM, structure)
3. Clone the skeleton to new parameters
4. LLM agent (Groq) generates remix instructions
5. Re-synthesize into new composition

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-song-decon.git
cd evez-song-decon
pip install -r requirements.txt
export GROQ_API_KEY=***
python decon.py
```

## API

```bash
# Deconstruct a song
curl -X POST http://localhost:8912/deconstruct \
  -F "file=@song.mp3"

# Get stems
curl http://localhost:8912/stems
```

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*