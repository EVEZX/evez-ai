# EVEZ OpenClaw — Offline Secure Deployment

Industry-standard offline deployment package for OpenClaw AI Gateway.
Self-contained. Air-gapped. Verified.

## What's Inside

| Component | Contents |
|-----------|----------|
| `bin/` | Node.js v22 runtime (standalone binary) |
| `openclaw-core/` | Complete OpenClaw 2026.6.8 installation |
| `config/` | Configuration template (API keys as env vars) |
| `skills/` | 78 skills (58 builtin + 5 plugin + 15 custom) |
| `install.sh` | One-command installer |
| `package.sh` | Archive builder with SHA-256 checksums |
| `verify.sh` | Integrity + security verification suite |
| `harden.sh` | Post-install security hardening |

## Quick Start

```bash
# Extract
tar xzf openclaw-offline-secure-*.tar.gz
cd openclaw-offline

# Verify integrity
chmod +x verify.sh && ./verify.sh

# Install
chmod +x install.sh && sudo ./install.sh /opt/openclaw

# Harden
chmod +x harden.sh && sudo ./harden.sh /opt/openclaw

# Start
sudo systemctl start openclaw-offline
```

## Security Model

- **Air-gapped**: No outbound connections required for core operation
- **Config template**: API keys injected via environment variables, never stored in package
- **SHA-256 verification**: Every file checksummed, archive checksummed
- **Principle of least privilege**: 0600 config, 0700 credentials, no world-readable secrets
- **fail2ban**: 3 SSH retries → 24h ban, 5 OpenClaw auth failures → 1h ban
- **SSH hardened**: Password auth disabled, root login disabled, 30s grace time
- **Firewall**: Default deny inbound, only 22/18789/443 open
- **Kernel**: SYN cookies, no ICMP redirects, no broadcast ping
- **Audit**: Config and credential file changes logged

## Architecture

```
/opt/openclaw/
├── bin/node                    # Node.js runtime
├── openclaw/                   # OpenClaw core
│   ├── openclaw.mjs           # Entry point
│   ├── dist/                  # Compiled JS
│   ├── skills/                # Built-in skills
│   └── node_modules/          # Dependencies
├── .openclaw/
│   ├── openclaw.json          # Configuration (0600)
│   ├── credentials/           # API keys (0700)
│   ├── cache/                 # Response cache
│   └── state/                 # Runtime state
└── skills/                    # Additional skill packages
```

## Compatibility

- **OS**: Ubuntu 22.04+, Debian 12+, any Linux with glibc 2.35+
- **Arch**: x86_64 (AMD64)
- **RAM**: 512MB minimum, 1GB recommended
- **Disk**: 500MB for core, 1GB with all skills
- **Network**: None required (offline mode), outbound for API calls

## Verification

Run `./verify.sh` to check:
1. File integrity (all files present)
2. SHA-256 checksums (no tampering)
3. Security (no leaked keys, correct permissions)
4. Runtime (Node.js functional)
5. Core modules (all required files)
6. Skills (packages available)
7. Network isolation (localhost-only binding)

## Built by EVEZ

Steven Crawford-Maggard | @EVEZ666 | EVEZX on GitHub
25 services · 49 models · $0/month
