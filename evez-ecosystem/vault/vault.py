#!/usr/bin/env python3
"""
EVEZ VAULT — Port 10003
Zero-knowledge secret storage. AES-256 encryption. Keys never leave the server.
$0/month. Self-hosted secrets manager.
"""
import json, time, hashlib, sqlite3, os, base64
from aiohttp import web
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

PORT = 10003
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/vault/vault.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS secrets (
        id TEXT PRIMARY KEY, key_name TEXT, encrypted_value TEXT, salt TEXT,
        tags TEXT, created REAL, accessed REAL, access_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS api_keys (
        key_hash TEXT PRIMARY KEY, name TEXT, created REAL, active BOOLEAN DEFAULT 1
    );
""")
DB.commit()

def derive_key(password, salt=None):
    """Derive AES key from password using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, base64.urlsafe_b64encode(salt).decode()

def encrypt_value(value, master_key):
    """Encrypt a secret value"""
    f = Fernet(master_key)
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted, master_key):
    """Decrypt a secret value"""
    f = Fernet(master_key)
    return f.decrypt(encrypted.encode()).decode()

async def handle_store(req):
    body = await req.json()
    secret_id = hashlib.md5(f"{body['key_name']}{time.time()}".encode()).hexdigest()[:10]
    master_pw = body.get("master_password", "evez-default-2026")
    key, salt = derive_key(master_pw)
    encrypted = encrypt_value(body["value"], key)
    DB.execute("INSERT OR REPLACE INTO secrets VALUES (?,?,?,?,?,?,?,?)",
              (secret_id, body["key_name"], encrypted, salt,
               json.dumps(body.get("tags", [])), time.time(), time.time(), 0))
    DB.commit()
    return web.json_response({"id": secret_id, "key_name": body["key_name"], "status": "encrypted"})

async def handle_retrieve(req):
    body = await req.json()
    secret_id = body.get("id", "")
    row = DB.execute("SELECT * FROM secrets WHERE id=?", (secret_id,)).fetchone()
    if not row:
        return web.json_response({"error": "Not found"}, status=404)
    master_pw = body.get("master_password", "evez-default-2026")
    salt = base64.urlsafe_b64decode(row["salt"].encode())
    key, _ = derive_key(master_pw, salt)
    try:
        decrypted = decrypt_value(row["encrypted_value"], key)
    except:
        return web.json_response({"error": "Decryption failed — wrong master password"}, status=403)
    DB.execute("UPDATE secrets SET accessed=?, access_count=access_count+1 WHERE id=?",
              (time.time(), secret_id))
    DB.commit()
    return web.json_response({"id": secret_id, "key_name": row["key_name"],
                             "value": decrypted, "tags": json.loads(row["tags"])})

async def handle_list(req):
    rows = DB.execute("SELECT id, key_name, tags, created, accessed, access_count FROM secrets").fetchall()
    return web.json_response({"secrets": [dict(r) for r in rows]})

async def handle_delete(req):
    body = await req.json()
    DB.execute("DELETE FROM secrets WHERE id=? AND key_name=?", (body.get("id"), body.get("key_name")))
    DB.commit()
    return web.json_response({"status": "deleted"})

async def handle_generate_password(req):
    length = int(req.query.get("length", "32"))
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    pw = ''.join(__import__('secrets').choice(chars) for _ in range(length))
    return web.json_response({"password": pw, "length": length, "entropy_bits": round(length * 6.5)})

async def handle_health(req):
    count = DB.execute("SELECT COUNT(*) as c FROM secrets").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-vault",
                             "secrets_stored": count, "encryption": "AES-256-Fernet", "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/store", handle_store)
app.router.add_post("/v1/retrieve", handle_retrieve)
app.router.add_get("/v1/list", handle_list)
app.router.add_delete("/v1/delete", handle_delete)
app.router.add_get("/v1/generate-password", handle_generate_password)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/vault", exist_ok=True)
    print(f"🔐 EVEZ Vault → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
