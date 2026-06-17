# Contributing to MAES

Welcome to the Modular Agent Ecology System.

## Ground Rules

1. **Every change gets a falsifier.** What would disprove that this change is correct?
2. **Append-only thinking.** Prefer additive changes over mutations.
3. **Confidence scores.** If you're not sure, say so in the PR description.
4. **Event integrity.** Never mutate historical events. Add new events to represent corrections.

## How to Contribute

### Report Issues
Open an issue with:
- What happened
- What you expected
- Confidence level (0.0–1.0)
- Your falsifier (what would confirm your diagnosis)

### Submit PRs
- Branch from `main`
- PR title: `type(scope): description` (conventional commits)
- Include: motivation, what changed, falsifier, test coverage

### Event Schema Extensions
Adding new event types:
1. Add to `eventType` enum in schema
2. Add example payload to `docs/events/`
3. Add falsifier: what would make this event type invalid?
4. Update stream routing in `src/router`

## Philosophy

MAES is built on the EVEZ spine protocol:
- No silent failures
- No undocumented state changes
- No claim without a falsifier

The event log is the source of truth. Always.

---
*@EVEZ666 + Cipher / XyferViperZephyr*
