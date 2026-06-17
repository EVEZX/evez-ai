# Autonomous execution protocol

## Intent
This protocol defines how self-piloted engineering loops should move from creator context to implementation, deployment, verification, revenue, and knowledge synchronization without fragmenting the system.

## Stage 1 — Anchor on creator
Read:
- `src/autonomy/creator_profile.json`
- `src/autonomy/research_bootstrap.md`
- `src/autonomy/agent_manifest.json`

Goal:
- resolve the operator identity first
- reconcile aliases and connected accounts
- avoid duplicate profiles and duplicate workstreams

## Stage 2 — Read implementation truth
Read the active repo surfaces and current registry state.
Primary code surfaces:
- `EvezArt/lord-evez/public/lord-monitor/`
- `EvezArt/Evez666/src/integrations/lord_bridge/`

Primary registry surfaces:
- Airtable `DEV_CIRCUIT_TASKS`
- Asana `EVEZ Connector Surfaces Continuation`
- Confluence continuation pages

Goal:
- determine what is already implemented
- determine what is blocked
- determine whether the blocker is code-side or environment-side

## Stage 3 — Attempt the narrowest meaningful change
Rules:
- prefer the smallest additive change that removes uncertainty
- prefer updating existing files and registries over creating parallel systems
- if deployment is blocked, create verification artifacts and operator routes rather than stalling

## Stage 4 — Persist the state transition
Every meaningful action must land in at least one durable surface in addition to chat.
Acceptable durable surfaces:
- GitHub commit
- Airtable record update
- Confluence page or continuation page
- Asana task note update
- Stripe object creation when commercialization is involved

## Stage 5 — Close the loop
After any change:
1. update the writable registry
2. update the durable runbook surface if state changed materially
3. update the planning layer if the blocker or next step changed
4. keep explicit distinction between:
   - implemented
   - deploy-ready
   - verification-ready
   - environment-blocked
   - commercially-live

## Current applied interpretation
At the time of writing:
- creator substrate exists
- LORD monitor exists
- LORD bridge exists
- verification artifacts exist
- commercial rails exist
- deployment remains environment-blocked at final authenticated Netlify proxy execution

## Non-negotiable constraints
- do not report a deployment as live unless it has actually been published
- do not create duplicate planning or registry systems when an existing one is writable
- do not erase governance when creating revenue surfaces
- do not detach the work from the creator context
