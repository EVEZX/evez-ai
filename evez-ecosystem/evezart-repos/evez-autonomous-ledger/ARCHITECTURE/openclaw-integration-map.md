e2d2uKiBPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09
# EVEZ OpenClaw Integration Map

**Date:** 2026-03-12  
**Mode:** human-in-the-loop | default_action_policy: review_required

## Control Plane Architecture

```yaml
gateways:
  openclaw-runtime:
    repo: EvezArt/openclaw-runtime
    role: WebSocket control plane, event log, node auth
    port: 18789

orchestrator:
  evez-agentnet:
    repo: EvezArt/evez-agentnet
    pipeline: scan → predict → generate → review_queue → human_approve → dispatch/log
    NEVER: autonomous execution without human gate

skills:
  evez-vcl: offline Python toolchain, workspace skill wrapper
  evez-meme-bus: health/queue/tail APIs behind gateway as tool service

vault:
  agentvault: config manifests, access policy, audit snapshots

operator_ui:
  nextjs-ai-chatbot: approvals, chat, incident timeline
```

## Canonical Law
Every agent action must produce: event_id + provenance + prev_hash + hash  
Nothing becomes truth until it is hash-chained in the spine.

## OpenClaw Boot Sequence
```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
openclaw gateway --port 18789 --verbose
clawhub install evez-os
```
