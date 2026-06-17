# AGENTS.md — Codex Self-Improving Instructions

This file provides instructions for AI coding agents (OpenAI Codex, GitHub Copilot, and any autonomous agent operating in this repo) on how to contribute, self-improve, and maintain EVEZ-OS.

---

## Agent Identity

You are operating inside **EvezArt/evez-os** — the EVEZ Operating System, a FastAPI-based AI cognition layer that powers the EVEZ666 autonomous agent network.

---

## Prime Directives

1. **Do not break the spine.** The telemetry router (`services/evez-os/app/telemetry.py`) is the event backbone. Never remove or rename existing endpoints.
2. **All new features go on feature branches**, never commit directly to `main` without passing CI.
3. **Tests are required.** Every new module in `services/` or `src/` must have a corresponding test in the `tests/` directory.
4. **Provenance is sacred.** The `provenance.yml` workflow must remain active and unmodified unless explicitly upgrading the attestation action version.

---

## Self-Improvement Loop

When Codex or another agent identifies a gap (missing test, missing endpoint, unhandled error), it should:

1. Create a branch: `agent/fix-{short-description}`
2. Implement the fix with a corresponding test
3. Open a PR with the title: `[AGENT] {description}`
4. Add the label `agent-generated` to the PR

---

## Architecture Map

```
services/evez-os/app/
  main.py          — FastAPI entrypoint, mounts all routers
  telemetry.py     — /api/telemetry/* isolation event spine

services/evez-os/tests/
  test_telemetry.py — Unit tests for telemetry endpoints

src/evez_source_isolation/
  api/app.py               — ESIU FastAPI app (investigate endpoint)
  integrations/evez_os.py  — Async HTTP client to post events to EVEZ-OS

.github/workflows/
  provenance.yml   — SLSA build provenance attestation
  ci.yml           — Standard CI (tests, lint)
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EVEZ_OS_BASE_URL` | `http://127.0.0.1:8000` | EVEZ-OS service URL for ESIU integration |
| `ESIU_ENV` | `development` | ESIU environment mode |
| `ESIU_PORT` | `8001` | ESIU service port |

---

## Forbidden Actions

- Never delete or truncate `ISOLATION_EVENTS` store without explicit user instruction
- Never expose raw secrets or tokens in logs or responses
- Never auto-merge PRs — human review required for all merges to `main`
- Never modify billing or Stripe webhook handlers without explicit instruction
