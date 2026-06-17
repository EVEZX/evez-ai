# OpenClaw Media Workstation

OpenClaw is now seeded with a runnable media-production layer instead of chat-only control. It can generate and deliver DAW-friendly artifacts from Linux/Ubuntu runtimes:

- WAV drum hits: kick, snare, closed/open hats, clap
- WAV bass/instrument samples
- 4-bar loop previews
- SFZ kit/instrument maps
- FL Studio FPC, Studio One Impact XT, and Ableton Drum Rack folder layouts
- ZIP sample packs for delivery/import
- Optional waveform preview videos through FFmpeg
- Optional remix/chop mode for 16-bit WAV inputs
- Direct Telegram local-file sending through Bot API multipart upload
- Artifact HTTP server for `mediaUrl` flows

## Host setup

```bash
./scripts/evez-openclaw-media-bootstrap.sh
```

This installs FFmpeg/Sox/FluidSynth/LAME/ZIP/JQ/Python media dependencies on apt/brew/apk systems where available, then creates a smoke-test kit.

## Generate a drum/instrument pack

```bash
./scripts/evez-openclaw-media-lab.sh --name evez_dark_kit --bpm 150
```

The output JSON reports the generated folder, `.zip`, loop WAV, SFZ, and preview video path if FFmpeg is present.

## Remix an existing WAV into a kit

```bash
./scripts/evez-openclaw-media-lab.sh --name remix_kit --remix /path/to/input.wav --slices 16
```

## Send generated media to Telegram

```bash
export TELEGRAM_BOT_TOKEN=...              # keep secret
export OPENCLAW_TELEGRAM_ALLOW_FROM=7453631330
./scripts/evez-openclaw-send-telegram-media.sh ~/.openclaw/media/evez_dark_kit.zip "OpenClaw kit"
./scripts/evez-openclaw-send-telegram-media.sh ~/.openclaw/media/evez_dark_kit/Previews/evez_dark_kit_waveform.mp4 "Preview"
```

This bypasses the old limitation where OpenClaw Telegram `sendMedia` expected a web `mediaUrl`; local files can now be uploaded directly as audio/video/document. For web-media flows, run:

```bash
./scripts/evez-openclaw-artifact-server.sh ~/.openclaw/media 18888
```

Then pass `http://<host>:18888/<artifact>` as a `mediaUrl` to OpenClaw outbound media.

## Nonlocal CPU/GPU runtimes

The Linux matrix image includes the media stack. Start the matrix:

```bash
./scripts/evez-openclaw-linux-matrix.sh up
```

On NVIDIA hosts with the NVIDIA Container Toolkit installed:

```bash
docker compose --env-file .env -f docker-compose.linux-matrix.yml -f docker-compose.gpu.yml up -d --build
```

The GPU override exposes compute/video capabilities to all OpenClaw runtime containers. The media scripts are CPU-safe by default and use FFmpeg acceleration when the host/container stack supports it.

## OpenClaw workspace seed

The workspace includes skill `evez-media-workstation` and tools under `workspace/tools/`, so onboarded OpenClaw agents can run the generator/sender directly from the seeded workspace.
