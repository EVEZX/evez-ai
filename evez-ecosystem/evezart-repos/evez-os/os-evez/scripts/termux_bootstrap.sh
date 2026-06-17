#!/usr/bin/env bash
# OS-EVEZ Termux Bootstrap
# Creator: Steven Crawford-Maggard (EVEZ666)
# github.com/EvezArt/evez-os
set -euo pipefail

echo "[OS-EVEZ] Bootstrapping on Termux..."

# 1. Storage
termux-setup-storage 2>/dev/null || echo "[skip] termux-setup-storage (non-Termux env)"

# 2. Packages
pkg update -y && pkg upgrade -y 2>/dev/null || apt-get update -y
for pkg in python git unzip curl tmux redis openssl libffi clang make pkg-config ffmpeg; do
  pkg install -y "$pkg" 2>/dev/null || apt-get install -y "$pkg" 2>/dev/null || echo "[warn] $pkg install skipped"
done

# 3. Data dir
export OG_DATA_DIR="${OG_DATA_DIR:-$HOME/og_data}"
mkdir -p "$OG_DATA_DIR/runs" "$OG_DATA_DIR/fixtures" "$OG_DATA_DIR/keys"          "$OG_DATA_DIR/ledger" "$OG_DATA_DIR/maps" "$OG_DATA_DIR/assets"
echo "OG_DATA_DIR=$OG_DATA_DIR" > "$HOME/.os_evez_env"

# 4. Python venv
cd "$(dirname "$0")/.."
python -m venv .venv
source .venv/bin/activate
pip install -U pip wheel setuptools
pip install -r requirements.txt || true

# 5. Generate Ed25519 keypair if missing
python - <<'PYEOF'
import os, json
from pathlib import Path
data_dir = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
key_file = data_dir / "keys" / "signing_key.json"
if not key_file.exists():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        priv_bytes = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()
        key_file.write_text(json.dumps({"private": priv_bytes, "public": pub}))
        print(f"[OS-EVEZ] Ed25519 keypair generated: {pub[:16]}...")
    except ImportError:
        import hmac, hashlib, secrets
        secret = secrets.token_hex(32)
        key_file.write_text(json.dumps({"mode": "mac", "secret": secret}))
        print("[OS-EVEZ] MAC signing key generated (cryptography not available)")
else:
    print("[OS-EVEZ] Key already exists.")
PYEOF

echo ""
echo "[OS-EVEZ] Bootstrap complete."
echo "  Data dir: $OG_DATA_DIR"
echo "  Next: bash scripts/termux_start_all.sh"
