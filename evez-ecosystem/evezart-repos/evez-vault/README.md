# EVEZ Vault — Autonomous Security & Encryption

Self-managing encryption and key rotation for the EVEZ stack.

## Quick Start

```bash
git clone https://github.com/EvezArt/evez-vault.git
cd evez-vault
pip install -r requirements.txt
python vault.py
```

## Features
- AES-256 encryption/decryption
- Automatic key rotation
- Secret management via environment variables
- Audit logging for all access
- Integration with EVEZ MAES event spine

## API

```bash
# Encrypt
curl -X POST http://localhost:8877/encrypt \
  -H "Content-Type: application/json" \
  -d '{"data": "sensitive text"}'

# Decrypt
curl -X POST http://localhost:8877/decrypt \
  -H "Content: application/json" \
  -d '{"token": "encrypted-token-here"}'
```

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*