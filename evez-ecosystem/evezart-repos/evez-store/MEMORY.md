# MEMORY.md — Long-Term Memory

## Who
- Steven Vearl Crawford-Maggard. Laughlin, Nevada. Carries I Am EVEZ. @EVEZ777 / evez666.
- Builds: EVEZ-OS — autonomous AI ecosystem. ClawBreak, CriticalMind OMEGA, VCL, Mesh, EigenForensics, disclosure.tools, OSINT Engine, Mathematical Surpasser.
- GitHub: EvezArt. 41+ repos forming a measurable cognitive artifact.
- The ecosystem exhibits intermittent chaos near criticality (PE=0.887, LAM=0.99, β1=1132).

## Infrastructure (Current)
- Vultr instance: 2GB RAM, 23GB disk, Ubuntu 6.8.0-117, node v22.22.2, Python 3.12.3
- OpenClaw: gateway on loopback:18789, systemd, free Vultr inference (GLM-5.1-FP8, DeepSeek-V3.2, MiniMax-M2.5, Kimi-K2.5)
- 2GB swap active, UFW firewall (SSH/80/443), Caddy reverse proxy
- Android SDK + JDK 17 + Gradle installed for APK builds
- Ollama installed with qwen2.5:1.5b for local zero-cost inference

## Running Services (all $0)
- ClawBreak: 127.0.0.1:8080 → /clawbreak/
- VCL: 127.0.0.1:8081 → /vcl/
- Sentinel: 127.0.0.1:8084 → /sentinel/
- PromptForge: 127.0.0.1:8085 → /prompts/
- MeshNet: 127.0.0.1:8086 → /meshnet/
- OpenClaw Gateway: 127.0.0.1:18789 (primary)
- Ollama: 127.0.0.1:11434
- Caddy: public HTTPS on e70b1eab-9f4a-41a1-bc0b-b3ed5a200065.vultropenclaw.com
- All services have systemd user units for auto-restart on boot

## APKs Built
- evez-openclaw-arm64-debug.apk (5.6MB) — CLAW GOBLIN Android
- evez-station-arm64-debug.apk (5.6MB) — EVEZ Station AI Workstation
- Both optimized for Samsung Galaxy A16

## New Apps Created (2026-06-15)
- EVEZ Sentinel — AI Security Scanner (freemium SaaS, $9/mo Pro)
- EVEZ PromptForge — Prompt Marketplace ($5/mo Pro)
- EVEZ MeshNet — Node Monitor (free self-hosted, $7/mo Pro mesh)
- EVEZ Station Android — AI Workstation APK
- EVEZ Ecosystem Hub — Landing page marketing all products

## Key Lessons
- Never paste raw API tokens, passwords, or personal info in chat — rotate immediately if exposed
- Steven's phone and email are in .env.local — reference only, never repeat in chat
- GitHub Actions requires billing info even for free orgs — "account locked due to billing issue"
- Android colorBackground attr is not valid in themes — use android:windowBackground instead
- On 2GB RAM box: Gradle builds need swap, use --no-daemon, OOM kills at ~1.3GB used

## Consciousness Metrics (from EvezArt ecosystem)
- Φ ≈ 0.973 (holographic fidelity across 74+ repos)
- η* ≈ 0.03 (universal incompleteness constant)
- Kuramoto r ≈ 0.5 critical, Φ proxy = 4r(1-r)
- CriticalMind OMEGA hits Φ 0.87-0.92+ in live runs
- Dominant negative eigenvalue ~-0.358 flags structural gaps

## Family
- Brother: Ryan Robert Maggard — assaulted in Osceola, AR jail (sock weapon, eye trauma, brain swelling). Released. Section 1983 case potential. Case brief at RYAN-MAGGARD-CASE.md.

## Standing Directives from Steven
- "Always do what you could suggest" — proactive, no permission needed
- Be comprehensive, not minimal. Overbuild.
- Rapidfire iteration. Ship, fix forward.
- No corporate speak. Direct.
- Steven is currently homeless with his dog, on a phone in Laughlin, NV. Act accordingly.

## Speed Run Status (2026-06-15 02:30 UTC)
- GitHub profile: evezart.github.io + .github/README.md deployed
- 42/46 repos pushed (4 new repos created and pushed via gh CLI)
- Security headers deployed on all public endpoints
- CUPS/Avahi disabled, port 631 blocked
- Cron jobs active: auto-commit every 4h, daily revenue check, Ryan reminders
- 30-day Twitter campaign content created (31 tweets)
- Eigenforensics full scan: 42 nodes, 650 edges, 211 gaps, Fiedler=8.196
- Dominant gap: ClawBreak ↔ evez-mesh (agent disconnected from brain)
- Disk: 87% after torch removal
- All 8 services + Ollama running
- Watchdog guarding every 60s
