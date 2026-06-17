# EVEZ-OS FULL CAPABILITY MAP v1.0
**Updated:** 2026-02-23T14:01 PST
**Scope:** Every connected app, what it can do, what's blocking it, workaround or gap route

---

## 🟢 ACTIVE — FIRING NOW

| App | Role | Actual Capability | Evez-OS Integration |
|-----|------|------------------|---------------------|
| **GitHub** | Spine | Commit files, read state, multi-file atomic commits | hyperloop_state.json, agent files, all workspace |
| **Hyperbrowser** | Probe | Browser-use tasks, gemini-2.0-flash, structured extraction | R141+ probe engine, EVEZ_COMPUTE tasks |
| **Twitter** | Publish | Post tweets, thread replies, video uploads | Content cron, arc videos, @EVEZ666 |
| **Vercel** | Host | Deploy, check status, env vars, domains | evez-autonomizer.vercel.app live |
| **ClickSend** | SMS | Send SMS to any number | R126 Steven +13076775504 |
| **Agenty** | Scrape | jQuery scrape any URL, structured data extract, browser JS execution | Polymarket scraper, GitHub trending |
| **OpenAI** | LLM | Chat completion, embeddings, moderation | Fallback LLM, embedding pipeline |
| **Perplexity AI** | Search | Real-time web search + synthesis | X semantic agent, signal detector |
| **YouTube** | Video | Upload video (via s3key), update metadata, thumbnails | Arc video pipeline — UNTAPPED |
| **All Images AI / Gemini** | Image Gen | Text→image, 1K/2K/4K, 9:16/16:9 ratios, Gemini Pro | Frame generation for videos |
| **Astica AI** | Vision | OCR on images, text extraction with bounding boxes | Frame annotation pipeline |
| **ElevenLabs** | TTS | 1000+ voices, eleven_v3 model, multilingual, 5000 chars/req | Voice narration for videos (NOT clone — pre-built voices only) |
| **Aivoov** | TTS | 1000+ voices across 150+ languages, ultra-tier voices | Voice fallback / multilingual narration |
| **Ably** | Realtime | Publish to channels, batch publish 100ch×1000msg, history | Live data bus for EVEZ Mirror |
| **Agenty** | Scrape | Browser JS execution, structured data, redirect tracing | Any web target |

---

## 🟡 AVAILABLE — NOT YET WIRED

| App | Role | What I can do with it TODAY | Gap Route |
|-----|------|----------------------------|-----------|
| **YouTube** | Long-form video | Upload full MP4 via s3key → publish to @lordevez channel | Wire: render arc video → upload_local_file → s3key → YOUTUBE_UPLOAD_VIDEO |
| **Gemini Image Gen** | Frame gen | Text→image per round → composite into video frames | Wire: SpawnBus frame_gen per tick |
| **Astica AI** | Frame vision | OCR frames → extract data → inject into video overlay | Wire: post-render annotation pass |
| **Ably** | Live bus | Publish hyperloop state on every tick → live dashboard subscribers | Wire: ably_config.json needed (just an API key) |
| **_2chat** | WhatsApp | Send WhatsApp messages to any number | Wire: mom's number + daily progress |
| **Google Cloud Vision** | Vision | Label detection, OCR, object localization, web detection on frames | Wire: billing toggle needed |
| **AI ML API** | Vision LLM | Multimodal LLM, image analysis | Wire: email verify at aimlapi.com |
| **Agenty** | Web intel | Scrape Polymarket, GitHub trending, any live data target | Wire: standalone scrape cron |
| **CloudConvert** | Media | Convert between 200+ formats, MP4↔GIF↔WebM | Wire: video format conversion |
| **Astica AI** | Caption | Caption generation for video frames | Wire: inject into video pipeline |
| **Google Maps** | Geo | Place data, directions, geocoding | Wire: geo-context for crisis OS |
| **Alchemy** | Blockchain | ETH/polygon on-chain data, NFT metadata, wallet analytics | Wire: blockchain intelligence layer |
| **Backendless** | DB | NoSQL database, user auth, file storage, real-time tables | Wire: backendless_config.json needed |
| **API Labz / Apiverve** | Misc APIs | Currency, weather, finance, IP, QR, many more | Wire: check available endpoints |
| **Agent Mail** | Email | Programmatic email agent, send/receive | Wire: standalone email pipeline |
| **Agenty** | Agent | Pre-built scraping agents | Wire: GitHub trending + Polymarket agents |

---

## 🔴 BLOCKED — NAMED GAPS WITH ROUTES

| App | Blocker | Gap Route | Action Owner |
|-----|---------|-----------|--------------|
| **ElevenLabs voice clone** | Paywall — /v1/voices/add blocked at API level | Use ElevenLabs pre-built voices (1000+) for narration NOW; clone deferred | Steven (upgrade) |
| **Ably** | `ably_config.json` missing — JWT key invalid | Create workspace/ably_config.json with API key from ably.com/accounts | Me (once key provided) |
| **Backendless** | `backendless_config.json` missing | Create workspace/backendless_config.json | Me (once keys provided) |
| **AI ML API** | Email verification at aimlapi.com | Complete email verify | Steven |
| **Google Cloud Vision** | Billing not enabled | Use Astica AI as Vision fallback (already wired) | Non-blocking |
| **Revenue $0** | GitHub Sponsors SSN enrollment | Complete github.com/sponsors/accounts | Steven |

---

## 🔥 HIGHEST LEVERAGE WIRES (DO RIGHT NOW)

### 1. YouTube Upload Pipeline
Arc videos are already rendering (PIL+ffmpeg). They're going to Twitter only.
**Gap:** upload_local_file → s3key → YOUTUBE_UPLOAD_VIDEO → @lordevez
**Result:** Every arc video cross-posts to YouTube automatically. Second distribution channel, zero extra work.

### 2. ElevenLabs Narration Track
Video frames are silent. ElevenLabs has 1000+ voices ready, eleven_v3 model, 70+ languages.
**Gap:** TTS narration of round stats → mix audio track → composite into MP4
**Result:** EVEZ videos have a voice. No clone needed — pick any voice from the 1000 available.

### 3. Gemini Image Gen per Round
Each hyperloop round gets a generated image: "prime lattice N=93, topo=1.30, fire_watch" → visual.
**Gap:** SpawnBus calls GEMINI_GENERATE_IMAGE on each tick → saves frame → injects into video composite
**Result:** Video frames have AI-generated visuals, not just matplotlib graphs.

### 4. Ably Live Bus
Real-time state on every tick. Subscribers see live V_global, ceiling, fire_watch updates.
**Gap:** Just need ably_config.json (API key). Get it from ably.com/accounts free tier.
**Result:** EVEZ becomes a live data feed anyone can subscribe to.

### 5. Astica AI Frame Annotation
Post-render: pass each video frame through Astica OCR → verify data legibility → auto-correct overlays.
**Gap:** Add post-render validation step in gen_video_inline.py
**Result:** Zero unreadable frames in arc videos.

### 6. YouTube + Twitter simultaneous post
Every arc video: Twitter reply AND YouTube upload, same render, zero extra render cost.

---

## ARCHITECTURE AFTER WIRES

```
hyperloop tick
  ↓
SpawnBus pre-writes next agent
  ↓
gemini image gen: frame for this round
  ↓
gen_video_inline.py: render arc (PIL+ffmpeg + image frames)
  ↓
ElevenLabs TTS: narration track → mix into MP4
  ↓
Astica: OCR verify all frames
  ↓
CloudConvert: MP4→WebM/GIF as needed
  ↓
upload_local_file → s3key
  ↓
├── Twitter: thread reply @EVEZ666
└── YouTube: upload @lordevez
  ↓
Ably: publish state update to evez-os channel
  ↓
MasterBus tick: ValidatorBus + MetaBus health check
```

Revenue wire (after Sponsors enrollment):
```
GitHub Sponsors webhook → agent_mail receives notification → ClickSend SMS to Steven
```
