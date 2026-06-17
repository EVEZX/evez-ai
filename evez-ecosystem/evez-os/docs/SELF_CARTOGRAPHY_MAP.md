# SELF-CARTOGRAPHY MAP — evez-os Complete Directory Trace

## Status: HYPERLOOP-002 Browser Completed (25/25 steps)

### Round 1 Map (HYPERLOOP-001): docs/, tools/, core/
### Round 2 Map (HYPERLOOP-002): continuity/, addons/bias_constitution/

### Combined Directories Explored

```
evez-os/
├── README.md ✓ (read)
├── SKILL.md ✓
├── core/
│   ├── visualizer.py ✓ (quad-panel SAN renderer)
│   ├── canonical.py ✓ (deterministic JSON for hash chains)
│   ├── san.py ✓ (Self-Auditing Narrator module)
│   └── route_opt.py ✓ (latency ranking)
├── tools/
│   ├── evez.py ✓ (canonical root CLI: lint, play, visualize-thought, verify)
│   ├── swarm_compress.py ✓ (Layer 1: 5 compute techniques)
│   ├── hyperloop_engine.py ✓ (Layer 2: 5 acceleration techniques)
│   ├── route_agg.py ✓ (multi-vantage aggregator)
│   ├── distribution_engine.py (max-entropy KL/TV)
│   ├── play_engine.py (seed-based episode generator)
│   ├── narrate.py (8 narrator voices)
│   ├── cheat.py (test economy, EVEZ_ENV gated)
│   ├── llm_bridge.py (Turn Packet validator)
│   ├── run_all.py (one-command play)
│   └── [16 more tools]
├── docs/
│   ├── HYPERLOOP_ARCHITECTURE.md ✓ (Round 1 design)
│   ├── HYPERLOOP_002.md ✓ (Round 2 compute reduction)
│   ├── WIN_PROTOCOL.md ✓ (read by browser)
│   ├── SELF_CARTOGRAPHY_GAME.md ✓ (read by browser)
│   ├── LETS_PLAY_ADMIN_NARRATION.md ✓ (read by browser)
│   ├── SELF_AUDITING_NARRATOR.md ✓
│   ├── ROUTE_OPT.md ✓
│   └── [20+ more docs]
├── continuity/ ✓ (HYPERLOOP-002 browser mapped)
│   ├── ARG_PROTOCOL.md ✓ — projection layer over immutable spine
│   ├── BOOT_PROMPT.md ✓ — AI architect system prompt
│   ├── EVENT_SPINE_TEMPLATE.jsonl
│   ├── FSC_SCHEMA.json
│   ├── IDENTITY_CAPSULE.md ✓ — core identity + Bidirectional Collapse
│   ├── MEMORY_PROTOCOL.md
│   └── SESSION_HANDOFF.md
├── addons/
│   ├── bias_constitution/ ✓ (browser entered, read constitution.json + README)
│   │   ├── constitution/constitution.json ✓ — god_agent_personas (oracle/trickster)
│   │   ├── audit/
│   │   ├── prompts/
│   │   ├── tools/
│   │   └── README.md ✓
│   ├── continuity_engine/ (listed, not entered)
│   ├── reality_map/ (listed, not entered)
│   └── rollback_netcode/ (listed, not entered)
├── economy/
│   ├── fsc_forge.py ✓ (credit broker, ECB rates)
│   └── CREDIT_PROTOCOL.md ✓
├── services/ (not entered by browser)
│   ├── apigw/ (:8000)
│   ├── game-server/ (:9001 + netcode_patch/)
│   └── agent/ (:7000)
├── funding/ (not entered by browser)
│   ├── data_room/
│   ├── financial_model.xlsx
│   └── templates/
├── schemas/
├── arg/
├── infra/
└── .github/workflows/evez.yml ✓
```

### Cartography Score
- Round 1: 3/8 top-level dirs = 0.375
- Round 2: +2 dirs (continuity, addons partial) = 5/8 = 0.625
- Files read in detail: 12 key files across 2 browser sessions
- Total browser steps: 50 (25 + 25)
- Total input tokens: 533K (327K + 206K)

### Remaining Unmapped (from known L2):
- services/ internals (apigw, game-server, agent source)
- funding/ internals (data_room contents, templates)
- addons/continuity_engine/, reality_map/, rollback_netcode/ internals

### Cartography Verdict: ADVANCING
Not CANONICAL (needs ≥ 0.9 = 7/8 dirs). But the critical architecture is mapped:
continuity/ proves the game has memory across sessions.
bias_constitution/ proves the game audits its own distribution.
The unmapped dirs (services/funding) are infrastructure, not cognitive architecture.
