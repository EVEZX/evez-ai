# Phone Quickstart (no laptop brain required)

If you're on a phone, you can still run this by doing **one** of these:

## Option A — Run locally later (best fidelity)
1. Download this zip.
2. On any computer:
```bash
unzip Game_Agent_Infra_EVEZ.zip
cd game-agent-infra-evz
docker compose up -d
```

## Option B — Use it as a *prompt kit* (works right now)
Copy/paste these 3 files into your next sessions:
- `continuity/BOOT_PROMPT.md`
- `continuity/IDENTITY_CAPSULE.md`
- `continuity/MEMORY_PROTOCOL.md`

Then keep appending to:
- `spine/EVENT_SPINE.jsonl`

## Daily ritual (30 seconds)
At the start of a session paste the BOOT prompt and the SESSION handoff.
At the end of a session paste the SESSION handoff updated + one FSC cycle JSON.

That's the 'remember across gaps' mechanism.


## ARG quick commands

- `python tools/evez.py arg-init`
- `python tools/evez.py arg-drop --lobby BGP --tag route-ghost --severity 3 --msg "The path you trusted is dead. Prove it."`
- `python tools/evez.py arg-narrate --tail 20`
