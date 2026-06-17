# Synapse Engine Integration

This repo is wired to the [EvezArt Synapse Engine](https://github.com/EvezArt/evez-synapse-engine).

## Trigger Operations via Synapse

Once the Synapse Engine is deployed to GCP, send payloads to your Cloud Run URL:

**Trigger this audit:**
```json
{"action": "audit_all", "repo": "EvezArt/evez-os", "ref": "main"}
```

**Create an issue:**
```json
{"action": "create_issue", "repo": "EvezArt/evez-os", "title": "EVEZ-OS Status", "body": "Synapse telemetry check."}
```

**Commit a file:**
```json
{"action": "commit_file", "repo": "EvezArt/evez-os", "path": "runtime/status.json", "content": "{\"status\": \"operational\"}", "message": "Synapse status update"}
```

Deploy the engine: `cd evez-synapse-engine && ./deploy.sh YOUR_GCP_PROJECT_ID`
