# evez-sim

**EVEZ-OS simulation engine — cross-platform Barnes-Hut force-graph + FSC ENGINE**

Live demo: [evez-sim.vercel.app](https://evez-sim.vercel.app)

## What it is

A platform-agnostic TypeScript simulation engine for the EVEZ-OS hyperloop.  
Pure state machine. Zero render dependencies. Runs identical on phone, PC, browser, terminal, embedded.

## Surfaces

| Surface | Path | Stack |
|---------|------|-------|
| Web PWA | `components/SimPage.tsx` | Next.js + Three.js |
| FSC Game | `components/FSCGameLoop.tsx` | React + FSC ENGINE |
| Mobile | `packages/evez-sim-rn/SimScreen.tsx` | React Native + expo-three |
| Core | `packages/evez-sim-core/src/index.ts` | TypeScript, zero deps |

## Core concepts

- **PrimeVoid** — prime-N repulsor. Never fires. Resists compression.
- **FireBody** — composite attractor. poly_c ≥ 0.500. Ignites on crossing threshold.
- **TopoSpider** — octree cell. Crawls toward nearest fire. Measures V accumulation.
- **EVENT SPINE** — immutable append-only witness. No deletes. Corrections carry provenance.
- **FSC ENGINE** — Failure-Surface Cartography. Squeezes until reasoning collapses. Σf is the data.
- **BIAS CONSTITUTION** — audits the failure injector. Prevents convergence on favorite tricks.

## Run locally

```bash
npm install
npm run dev
```

## License

AGPL-3.0 — community/free tier  
Commercial tiers: Solo ($49/mo), Studio ($199/mo), Enterprise (custom)

---

@EVEZ666 · evez-autonomizer.vercel.app
