"""
Nomad Vault — encrypted local credential store for EVEZ-OS mesh.
Uses Fernet symmetric encryption. Key derived from machine identity.
"""
import os
import json
import hashlib
import base64
from pathlib import Path
from cryptography.fernet import Fernet

VAULT_PATH = Path(os.environ.get("EVEZ_VAULT_PATH", "~/.evez_vault.enc")).expanduser()
KEY_PATH   = Path(os.environ.get("EVEZ_KEY_PATH",   "~/.evez_vault.key")).expanduser()

def _derive_key() -> bytes:
    """Derive encryption key from machine fingerprint."""
    fingerprint = (
        os.environ.get("EVEZ_VAULT_SEED") or
        os.uname().nodename + os.environ.get("USER", "evez") + "EVEZ666"
    )
    raw = hashlib.sha256(fingerprint.encode()).digest()
    return base64.urlsafe_b64encode(raw)

def _fernet() -> Fernet:
    if KEY_PATH.exists():
        key = KEY_PATH.read_bytes()
    else:
        key = _derive_key()
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        KEY_PATH.write_bytes(key)
        os.chmod(KEY_PATH, 0o600)
    return Fernet(key)

def _load_vault() -> dict:
    if not VAULT_PATH.exists():
        return {}
    try:
        encrypted = VAULT_PATH.read_bytes()
        decrypted = _fernet().decrypt(encrypted)
        return json.loads(decrypted)
    except Exception:
        return {}

def _save_vault(data: dict):
    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    encrypted = _fernet().encrypt(json.dumps(data).encode())
    VAULT_PATH.write_bytes(encrypted)
    os.chmod(VAULT_PATH, 0o600)

def save_config(key: str, value: str):
    """Save a credential to the vault."""
    data = _load_vault()
    data[key] = value
    _save_vault(data)
    print(f">> Saved: {key}")

def load_config(key: str, default=None) -> str:
    """Load a credential. Falls back to env var, then default."""
    env_val = os.environ.get(key)
    if env_val:
        return env_val
    data = _load_vault()
    return data.get(key, default)

def list_keys() -> list:
    return list(_load_vault().keys())

def delete_config(key: str):
    data = _load_vault()
    if key in data:
        del data[key]
        _save_vault(data)
        print(f">> Deleted: {key}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "set":
        key, val = sys.argv[2].split("=", 1)
        save_config(key, val)
    elif len(sys.argv) == 3 and sys.argv[1] == "get":
        print(load_config(sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        for k in list_keys():
            print(k)
    elif len(sys.argv) == 1:
        print("Nomad Vault — interactive setup")
        KEYS = [
            "TELEGRAM_BOT_TOKEN", "OPENROUTER_API_KEY", "GROQ_API_KEY",
            "GITHUB_PAT", "VERCEL_TOKEN", "CLOUDFLARE_API_TOKEN",
            "CLOUDFLARE_ACCOUNT_ID", "FLY_API_TOKEN", "MEM0_API_KEY",
            "STRIPE_SECRET_KEY", "NGROK_AUTHTOKEN", "OPENCLAW_GATEWAY_TOKEN",
        ]
        for k in KEYS:
            existing = load_config(k)
            prompt = f"  {k} [{('***set***' if existing else 'not set')}]: "
            val = input(prompt).strip()
            if val:
                save_config(k, val)
        print("\n>> Vault updated.")
    else:
        print("Usage: python nomad_vault.py [set KEY=VALUE | get KEY | list]")