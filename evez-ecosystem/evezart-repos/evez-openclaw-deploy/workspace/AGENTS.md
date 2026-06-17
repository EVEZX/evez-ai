# EVEZ OpenClaw Agent Configuration

## Default Model

`groq/llama-3.3-70b-versatile` when `GROQ_API_KEY` is configured.

Fallbacks configured by onboarding:
1. `openrouter/meta-llama/llama-3.3-70b-instruct:free`
2. `openrouter/openai/gpt-oss-20b:free`
3. `openrouter/qwen/qwen3-coder:free`
4. `groq/llama-3.1-8b-instant`

If only OpenRouter is configured, onboarding promotes OpenRouter to primary.

## Loaded baseline plugins

Generated config enables:

- `memory-core`
- `llm-task`
- `telegram` when `TELEGRAM_BOT_TOKEN` exists or existing config had Telegram enabled
- `slack` when `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` exist or existing config had Slack enabled
- `open-prose`
- `copilot-proxy`
- `lobster` — bundled host-compatible Lobster plugin

## Workspace skills

- `clawdhub` — verified ClawHub skill for ClawdHub CLI usage.
- `lobster` — verified ClawHub skill for deterministic typed workflows and approval gates.

## EVEZ context

- Identity seed: `EVEZ_IDENTITY.md`
- Public repo inventory: `ecosystem/github-public-repos.json`
- Optional private local-only repo inventory: `private/github-visible-repos-private.json`

## Channels

- Telegram: enabled when token is present and allowlist configured.
- Slack: config slots are preserved; enable by providing Slack bot/app tokens.

## Operating rules

- Use real upstream OpenClaw Gateway + Control UI; do not substitute a custom dashboard.
- Keep secrets in `openclaw.env` or provider dashboards, never in git.
- Use Lobster approval gates before side-effecting multi-step automations.
- Prefer action and concrete recovery checks over long explanation.
