# Agent Bus — Module 03
## Crew definitions, Peace Charter, bus topology

### Peace Charter (binding on all agents)

1. Defense-only: monitor/warn/coordinate/recommend — never direct harm
2. Witness before will: ≥2 independent evidence lines before strong action
3. Human sovereignty: Steven can halt any agent instantly
4. Typed events only: nothing enters spine as free-form text
5. Transparent lanes: empirical never masquerades as metaphysical
6. No silent rotation: W0 identity never changes without human confirmation
7. Reversibility preference: choose more reversible action when equal

### 4 Crew Roles

| Role | Layer | Emits | Tools |
|------|-------|-------|-------|
| SENSOR | observation | observation events | Twitter search, GitHub, HTTP health |
| PREDICTOR | reasoning | transformation, claim | Groq, Perplexity, canonicalize API |
| REFEREE | test/decision | test, decision | contradiction API, spine verify |
| MESSENGER | output | linkage | Twitter post, Alchemy tx, Backendless |

### Bus Topology
```
World → [SENSOR] → [PREDICTOR] → [REFEREE] → [MESSENGER] → World
           ↓           ↓              ↓              ↓
                    [SPINE] ←────────────────────────┘
```

### Circuit Breaker
- 71+ consecutive failures → agent STOPS
- Emits decision event: circuit_breaker_open
- Human must confirm restart — no auto-restart