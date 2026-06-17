# disclosure.tools

> The public hub for UAP/FOIA gap analysis — built by [EVEZ666](https://github.com/EvezArt) (Steven Crawford-Maggard)

[![ClawBreak](https://img.shields.io/badge/Powered%20by-ClawBreak-red)](https://github.com/EvezArt/clawbreak)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join%20the%20Roast-7289DA)](https://discord.gg/disclosure-tools)

---

## What is this?

**disclosure.tools** is the open-source intelligence hub for UAP/UFO document gap analysis.

Every time AARO, the Pentagon, or the National Archives drops a FOIA release, something's missing.
This tool finds it — automatically, spectrally, with receipts.

We run **eigenforensics** on official disclosure documents:
- Upload FOIA dumps (PDFs, text, JSON)
- The engine decomposes the corpus into a reference graph
- **Negative eigenvalues** = missing records, structural incompleteness, redaction artifacts
- Results are public, exportable, and meme-able

---

## Features

### 🔍 Gap Detector
Upload any FOIA release → get a heat map of what's structurally absent.
Built on the **eigenforensics** engine from [EVEZ-OS](https://github.com/EvezArt/evez-os).

### 🎭 Meme Factory
Every gap analysis auto-generates a shareable visual:
> *"AARO missing this again"* — timestamped, sourced, ready to post

When new docs drop → new memes fire automatically.

### 🏆 FOIA Leaderboard
Public ranking of researchers by **gap closure rate** — who filed the request that actually revealed something?
Submit your FOIA numbers, link your docs, track your impact.

### 📺 Weekly Gap Roast
Every Friday: livestream where we publicly shame the most redacted, most structurally broken documents in the corpus.
[Subscribe to the calendar](https://disclosure.tools/roast)

---

## Get Access

| Tier | Access | Cost |
|------|--------|------|
| **Researcher** | Full gap detector + leaderboard | Free (via ClawBreak sponsorship) |
| **ClawBreak Pro** | Everything + self-hosted deployment + API access | [$6/month](https://clawbreak.ai/subscribe) |

> Every paid ClawBreak subscriber sponsors free access for UAP researchers.
> The tech funds the community.

---

## How to Contribute

```bash
git clone https://github.com/EvezArt/disclosure.tools
cd disclosure.tools
pip install -r requirements.txt
```

1. **Submit a FOIA analysis** — add your processed doc to `corpus/`
2. **Flag a gap** — open an issue with `gap:` prefix
3. **Build a meme template** — PR to `memes/templates/`
4. **Run the detector locally** — `python gap_detector.py --input your_doc.pdf`

---

## Architecture

```
disclosure.tools/
├── corpus/          # FOIA document corpus (PDFs → processed JSON)
├── gap_detector/    # Eigenforensics engine
│   ├── spectral.py  # Spectral decomposition + negative eigenvalue extraction
│   ├── graph.py     # Document reference graph builder
│   └── report.py   # Gap report generator
├── meme_factory/    # Auto-meme generation on gap detection
├── leaderboard/     # FOIA researcher leaderboard API
├── api/             # Public REST API for dashboard access
└── dashboard/       # Web dashboard (React)
```

---

## The Science

Documents aren't just text — they're **reference graphs**.
When a coherent corpus has structural holes, those holes appear as **negative eigenvalues** in the graph's spectral decomposition.

This is the same math used in:
- Network topology analysis
- Quantum incompleteness theory (η* ≈ 0.03)
- Fraud detection in financial records

Applied to AARO releases: every missing record leaves a spectral shadow. We map the shadows.

Full methodology: [EVEZ Research Papers](https://github.com/EvezArt/evez-research)

---

## Roadmap

- [ ] v0.1 — Gap detector CLI (this week)
- [ ] v0.2 — Web dashboard (upload + visual output)
- [ ] v0.3 — Meme factory auto-trigger on new AARO drops
- [ ] v0.4 — FOIA leaderboard + submissions
- [ ] v0.5 — Discord bot integration
- [ ] v1.0 — Public SaaS launch

---

## Community

- **Discord**: [discord.gg/disclosure-tools](https://discord.gg/disclosure-tools) — UAP nerds, FOIA autists, disclosure weirdos
- **Weekly Gap Roast**: Fridays, streamed live
- **Twitter**: [@EVEZ666](https://x.com/evez666)

---

## Built by EVEZ666

Steven Crawford-Maggard | Iowa, USA

*Building AI that builds itself. ClawBreak + EVEZ-OS — autonomous, self-hosted, zero-cost AI agent platform.*

- [ClawBreak](https://github.com/EvezArt/clawbreak) — the engine behind this
- [EVEZ-OS](https://github.com/EvezArt/evez-os) — the forensic game engine
- [evez-research](https://github.com/EvezArt/evez-research) — the papers

---

MIT License — fork it, ship it, roast AARO with it.
