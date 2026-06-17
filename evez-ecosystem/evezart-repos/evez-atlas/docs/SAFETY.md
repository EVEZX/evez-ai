# Safety Guardrails for Self-Automation

This repository contains automation that can create artifacts, update docs, and run scheduled checks. The default stance is **SAFE_MODE ON**, meaning the system may generate proposals and evidence, but must not take irreversible or external actions without explicit human approval.

## Principles

Autonomy is allowed only when it is (1) reversible, (2) auditable, and (3) least-privilege. Any workflow that can change repository state, post externally, or touch payments must be gated behind human approval and must never run on untrusted triggers.

## Allowed autonomous actions (default)

The system may run tests, static analysis, linting, dependency audits, and generate *proposed* content (markdown drafts, JSON reports, checklists) that is stored as artifacts or committed only via a PR.

## Disallowed without approval

External posting (X/Reddit/HN/YouTube), sending emails/DMs, creating paid products, charging/billing, and any action that moves money are disallowed unless (a) approved via manual workflow dispatch or environment approval, and (b) the workflow clearly documents what it will do.

## Required workflow rules

- No `pull_request_target` unless explicitly approved and narrowly scoped.
- Workflows must declare explicit `permissions:` and avoid broad write permissions.
- Secrets must never be printed to logs; prefer masked secrets and short-lived tokens.
- Any network egress beyond GitHub APIs must be allowlisted and must run in SAFE_MODE by default.

## SAFE_MODE

All automation code that can post externally or change monetization settings must support an env var `SAFE_MODE` (default `true`). In SAFE_MODE, the system should produce the content it *would* post, but not actually post.
