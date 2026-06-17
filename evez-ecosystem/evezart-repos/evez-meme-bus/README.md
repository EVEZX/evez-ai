# EVEZ Meme Bus

Append-only constitutional meme pipeline. Drop images → get Christ/antichrist/end-times captions filtered through PeaceKernel → memes rendered and logged to the EventSpine.

## Quick start

```bash
chmod +x deploy-all.sh stop-all.sh
./deploy-all.sh
```

Set `OPENAI_API_KEY` for live LLM captions, or run in stub mode (3 hardcoded captions).

## Pipeline

```
assets/input_images/  →  ImageIngestor  →  CaptionAgent  →  ConstitutionalGuard  →  LayoutAgent  →  Publisher  →  assets/output_memes/
```

## API

- `GET /healthz` — liveness
- `GET /queue-status` — event counts by kind
- `GET /tail?n=20` — last N events
- `GET /drafts` — approved meme output files

## Event spine

All events are appended to `src/memory/meme_events.jsonl` with SHA-256 hash chain (prevHash → hash).
