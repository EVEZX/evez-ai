# OS-EVEZ Security Model

Creator: Steven Crawford-Maggard (EVEZ666)

## Capability Model (Default-Deny)

All capabilities are OFF by default. Only allowlisted operations execute.

| Capability | Default | Allowlist |
|-----------|---------|-----------|
| FS_READ | DENY | ./runs, ./fixtures, ./state |
| FS_WRITE | DENY | ./runs, ./state |
| SHELL | DENY | ls, cat, echo, python, ffmpeg |
| NET_OUT | DENY | disabled entirely |

## Kill Switch

Create `$OG_DATA_DIR/STOP` to immediately halt:
- autoclaw scheduler
- speeddaemon
- all bounded loops

```bash
touch $OG_DATA_DIR/STOP         # stop
rm $OG_DATA_DIR/STOP            # resume
```

## Budgets

Every scheduler run is bounded:
- `max_runtime_seconds`: 1800
- `max_disk_mb`: 512 (per sandbox)
- `max_tool_calls`: 1000 (per session)
- `retention_runs`: 80 (prune oldest)
- `max_disk_mb` (global): 4096

## API Key Safety

- OPENAI_API_KEY: read from server env ONLY
- Never committed to git
- Never exposed in browser/mobile UI
- OpenClaw model client is server-side only

## Signing + Provenance

Every run_bundle.zip includes:
- provenance/ATTRIBUTION.md (creator, handle, repo, license)
- provenance/bundle_manifest.json (root_hash + Ed25519 signature)
- /public-key.html: verify bundles against this key

## What OS-EVEZ Does NOT Do

- No network scanning
- No exploitation or persistence
- No self-spread or "conquest"
- No bypassing capability gates
- No storing or transmitting API keys
