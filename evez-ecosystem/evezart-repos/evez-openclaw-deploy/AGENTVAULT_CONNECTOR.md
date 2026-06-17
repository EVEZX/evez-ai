# AgentVault Connector Runtime Profile

Steven's requested AgentVault connector profile is staged in `runtime/agentvault-connector.json`:

```json
{
  "module": "agentvault-connector",
  "version": "1.3.5",
  "vault": {
    "attestation": "tpm2",
    "audit_log": true,
    "rotation_interval_hours": 24,
    "zero_knowledge": true
  }
}
```

It is intentionally kept outside `openclaw.json` because OpenClaw rejects unknown config keys. The onboarding script copies it into the local OpenClaw state directory as `~/.openclaw/agentvault-connector.json`, where a host-side AgentVault service/sidecar can consume it without breaking Gateway validation.

Operational intent:
- TPM2-backed attestation when the host has TPM2 available
- audit log enabled
- 24-hour secret rotation policy
- zero-knowledge secret handling
- no secrets committed to git
