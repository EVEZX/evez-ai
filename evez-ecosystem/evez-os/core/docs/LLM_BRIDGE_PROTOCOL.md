# LLM BRIDGE PROTOCOL v1

This document defines the portable interchange format between:
- Human (player/prompter)
- LLM (narrator/analyst)
- Local runner (validator + append-only spine writer)

The goal is to make the game **cross-platform** (ChatGPT, Perplexity, etc.)
by removing authority from the model and placing it in deterministic tooling.

---

## Objects

### 1) Turn Packet (LLM output)
A Turn Packet is a JSON object with these top-level keys:

- `episode`: `{ seed:int, step:int, lobby:str }`
- `claims`: list of Claim objects
- `probes`: list of ProbeRequest objects
- `sigma_f`: list[str]
- `omega`: list[str]
- `next`: str

### 2) Claim
`{ id:str, text:str, truth_plane: "TRUTH"|"PENDING"|"THEATER", provenance:str, falsifier:str, confidence: float }`

**Validation rule:** if `truth_plane=="TRUTH"`, both `provenance` and `falsifier` must be non-empty and specific.

### 3) ProbeRequest
`{ type:str, target:str, vantage_id:str, why_this_probe:str }`

Local runner maps `type` to real probe implementations (dns/http/tls/ping/etc.).

---

## Mapping to Spine Events

Local runner appends:

- `kind: llm.turn`
- `kind: llm.claim`
- `kind: llm.probe_request`

Each event includes:
- `ts` ISO timestamp
- `trace_id` content-hash of canonical JSON for the object
- `vantage_id` when relevant

---

## Safety Constraint

The local runner MUST reject outputs that provide:
- exploitation steps
- credential theft
- stealth/persistence instructions
- “hidden access / backdoor discovery” attempts on systems not explicitly owned and authorized for testing

Instead, the model should be routed to **sandboxed, authorized testbeds** (VMs, CTFs, intentionally vulnerable images) and **defensive measurement**.

