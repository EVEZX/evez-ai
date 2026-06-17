---
name: evez-media-workstation
description: Generate and send DAW-friendly OpenClaw media: WAV samples, drum kits, SFZ instruments, loop previews, videos, ZIP packs, and Telegram media artifacts.
---

# EVEZ Media Workstation

Use this skill when Steven asks OpenClaw to make music samples, custom drum kits, instrument packs, preview videos, or Telegram-deliverable media.

## Tools

- `workspace/tools/evez-media-lab.py` — generates WAV drums, bass/instrument samples, SFZ maps, DAW folder layouts, ZIP packs, and optional FFmpeg waveform videos.
- `workspace/tools/evez-send-telegram-media.sh` — sends a local generated file through Telegram Bot API as photo/video/audio/document. Requires `TELEGRAM_BOT_TOKEN` and `OPENCLAW_TELEGRAM_ALLOW_FROM` or `TELEGRAM_CHAT_ID`.
- `workspace/tools/evez-artifact-server.sh` — serves generated artifacts over HTTP so OpenClaw/Telegram `mediaUrl` flows can fetch them.

## Examples

```bash
python3 workspace/tools/evez-media-lab.py --name dark_evez_drums --bpm 150 --out-dir "$OPENCLAW_MEDIA_DIR"
python3 workspace/tools/evez-media-lab.py --name remix_pack --remix /path/to/input.wav --slices 16 --out-dir "$OPENCLAW_MEDIA_DIR"
workspace/tools/evez-send-telegram-media.sh "$OPENCLAW_MEDIA_DIR/dark_evez_drums.zip" "OpenClaw drum kit"
```

Generated packs include:

- `Samples/Drums/*.wav`
- `Samples/Instruments/*.wav`
- `Kits/*.sfz`
- `Loops/*_4bar.wav`
- `FL_Studio_FPC/`, `StudioOne_ImpactXT/`, `Ableton_DrumRack/` layouts
- `manifest.json`
- `.zip` archive for sending/importing
