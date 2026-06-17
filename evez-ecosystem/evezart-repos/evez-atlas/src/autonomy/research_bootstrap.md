# Autonomous engineering bootstrap

## Purpose
This file gives autonomous development and research loops a stable starting context. It is not a complete biography. It is a practical operating brief for systems that need to build, verify, document, deploy, and monetize without re-deriving the creator profile from scratch.

## Start with the creator
The creator and operator identity to anchor on is **Steven Crawford-Maggard (EVEZ)**.
Aliases already in active use across connected systems:
- EVEZ
- Evez666
- EvezArt

Use the machine-readable profile in `src/autonomy/creator_profile.json` as the primary identity source.

## Working assumptions
1. GitHub is the code source of truth.
2. Airtable `DEV_CIRCUIT_TASKS` is the execution registry.
3. Asana `EVEZ Connector Surfaces Continuation` is the visible planning layer.
4. Confluence continuation pages are the durable runbook layer.
5. Stripe is live and already contains active commercial rails.
6. Netlify is the intended deployment target for the LORD monitor surface.

## Current active build surfaces
### LORD Monitor
- Repo: `EvezArt/lord-evez`
- Path: `public/lord-monitor/`
- Current state: implemented, deploy-ready, publish still pending

### LORD Bridge
- Repo: `EvezArt/Evez666`
- Path: `src/integrations/lord_bridge/`
- Current state: implemented, verification assets ready, awaiting live browser-to-runtime test

## First research priorities
1. Track all creator aliases and linked execution surfaces.
2. Track all active repos, deployment targets, and blockers.
3. Track all payment rails and offer ladders that are already live.
4. Track all verification artifacts and operator runbooks.
5. Avoid duplicating systems that already exist in GitHub, Airtable, Asana, Confluence, Stripe, or Netlify.

## Behavioral rules for autonomous loops
- Prefer updating existing systems over creating duplicates.
- Persist every meaningful change into a writable system of record.
- Distinguish implementation blockers from execution-environment blockers.
- Treat the creator profile as operational context, not as a target for invasive profiling.
- When commercialization surfaces are involved, keep governance and tracking attached.

## Immediate next actions for future agents
1. Read `creator_profile.json`.
2. Read the current Airtable records for LORD monitor, LORD bridge, and revenue rails.
3. Read the Confluence continuation page for the latest deployment state.
4. Attempt deployment only through authenticated, permitted execution paths.
5. After live publish, complete the bridge verification loop and mark records complete.
