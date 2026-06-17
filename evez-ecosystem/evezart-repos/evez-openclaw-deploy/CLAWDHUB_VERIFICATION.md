# Clawdhub Skill Verification

Verified before install:

- ClawHub page: `https://clawhub.ai/steipete/clawdhub`
- Owner shown by ClawHub: Peter Steinberger / `steipete`
- Skill slug/version: `clawdhub` `1.0.0`
- Security audit status shown by ClawHub: `Review`
- Download endpoint returned `clawdhub-1.0.0.zip`
- Archive files: `SKILL.md`, `_meta.json`, `skill-card.md`
- `_meta.json`: ownerId `kn70pywhg0fyz996kpa8xj89s57yhv26`, slug `clawdhub`, version `1.0.0`
- Skill metadata requirement: binary `clawdhub`; install spec kind `node`, package `clawdhub`, bin `clawdhub`

CLI package check:

- npm package: `clawdhub`
- Stable `0.3.0` was inspected and had no lifecycle install scripts, but its dependency list omitted `undici` while runtime imports it.
- `0.3.1-beta.1` was inspected before use; it adds `undici`, has no preinstall/postinstall scripts, and exposes only `bin/clawdhub.js`.
- Installed CLI: `clawdhub --cli-version` = `0.3.1-beta.1`.

Live install performed:

```bash
clawdhub --site https://clawhub.ai --registry https://clawhub.ai --workdir /work/openclaw-state/workspace --dir skills install clawdhub --version 1.0.0 --force
```

OpenClaw verification:

- `openclaw skills list` shows workspace skill `clawdhub` from `openclaw-workspace`.
- `openclaw skills check` shows `clawdhub` in Ready to use.
