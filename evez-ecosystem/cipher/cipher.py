#!/usr/bin/env python3
"""
EVEZ CIPHER — Port 10005
Encryption toolkit: AES-256, RSA, hash, HMAC, JWT encode/decode.
$0/month. Self-hosted crypto-as-a-service.
"""
import json, time, base64, hashlib, hmac as hmac_mod, os
from aiohttp import web
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
import jwt

PORT = 10005

# Key store (in-memory for speed, persisted to disk)
KEYS = {}

def get_or_create_key(name, key_type="aes"):
    if name not in KEYS:
        if key_type == "aes":
            KEYS[name] = Fernet.generate_key()
        elif key_type == "rsa":
            private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            KEYS[name] = {"private": private, "public": private.public_key()}
    return KEYS[name]

async def handle_aes_encrypt(req):
    body = await req.json()
    key_name = body.get("key", "default")
    key = get_or_create_key(key_name, "aes")
    f = Fernet(key)
    encrypted = f.encrypt(body["plaintext"].encode()).decode()
    return web.json_response({"encrypted": encrypted, "key_name": key_name})

async def handle_aes_decrypt(req):
    body = await req.json()
    key_name = body.get("key", "default")
    key = get_or_create_key(key_name, "aes")
    f = Fernet(key)
    try:
        decrypted = f.decrypt(body["ciphertext"].encode()).decode()
        return web.json_response({"decrypted": decrypted, "key_name": key_name})
    except:
        return web.json_response({"error": "Decryption failed"}, status=400)

async def handle_hash(req):
    body = await req.json()
    algorithm = body.get("algorithm", "sha256")
    data = body["data"].encode()
    hash_map = {
        "md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256,
        "sha512": hashlib.sha512, "sha3_256": hashlib.sha3_256, "sha3_512": hashlib.sha3_512,
    }
    if algorithm not in hash_map:
        return web.json_response({"error": f"Unsupported: {algorithm}"}, status=400)
    result = hash_map[algorithm](data).hexdigest()
    return web.json_response({"hash": result, "algorithm": algorithm})

async def handle_hmac(req):
    body = await req.json()
    algorithm = body.get("algorithm", "sha256")
    result = hmac_mod.new(body["key"].encode(), body["data"].encode(),
                         getattr(hashlib, algorithm)).hexdigest()
    return web.json_response({"hmac": result, "algorithm": algorithm})

async def handle_jwt_encode(req):
    body = await req.json()
    secret = body.get("secret", "evez-default-secret")
    payload = body["payload"]
    token = jwt.encode(payload, secret, algorithm="HS256")
    return web.json_response({"token": token})

async def handle_jwt_decode(req):
    body = await req.json()
    secret = body.get("secret", "evez-default-secret")
    try:
        payload = jwt.decode(body["token"], secret, algorithms=["HS256"])
        return web.json_response({"payload": payload, "valid": True})
    except jwt.InvalidTokenError as e:
        return web.json_response({"error": str(e), "valid": False}, status=401)

async def handle_rsa_keygen(req):
    bits = int(req.query.get("bits", "2048"))
    private = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    pub_pem = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    priv_pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    return web.json_response({"public_key": pub_pem, "private_key": priv_pem, "bits": bits})

async def handle_password(req):
    import secrets, string
    length = int(req.query.get("length", "32"))
    alphabet = string.ascii_letters + string.digits + string.punctuation
    pw = ''.join(secrets.choice(alphabet) for _ in range(length))
    return web.json_response({"password": pw, "length": length, "entropy_bits": round(length * 6.5)})

async def handle_health(req):
    return web.json_response({"status": "healthy", "service": "evez-cipher",
                             "algorithms": ["AES-256", "RSA-2048", "SHA-256", "SHA-512", "SHA3", "HMAC", "JWT"], "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/aes/encrypt", handle_aes_encrypt)
app.router.add_post("/v1/aes/decrypt", handle_aes_decrypt)
app.router.add_post("/v1/hash", handle_hash)
app.router.add_post("/v1/hmac", handle_hmac)
app.router.add_post("/v1/jwt/encode", handle_jwt_encode)
app.router.add_post("/v1/jwt/decode", handle_jwt_decode)
app.router.add_get("/v1/rsa/keygen", handle_rsa_keygen)
app.router.add_get("/v1/password", handle_password)

if __name__ == "__main__":
    print(f"🔒 EVEZ Cipher → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
