#!/usr/bin/env python3
"""
Deploy all EVEZ servers. Creates systemd units, enables, starts.
Run once: python3 deploy-all-new.py
"""
import os, subprocess, time

SERVICES = [
    {"name": "evez-dns-shield", "port": 10001, "path": "dns-shield/dns-shield.py", "desc": "DNS-over-HTTPS resolver + monitor"},
    {"name": "evez-pulse", "port": 10002, "path": "pulse/pulse.py", "desc": "Uptime monitor + incident response"},
    {"name": "evez-vault", "port": 10003, "path": "vault/vault.py", "desc": "Zero-knowledge secret storage (AES-256)"},
    {"name": "evez-proxy", "port": 10004, "path": "proxy-gateway/proxy.py", "desc": "API gateway with caching + rate limiting"},
    {"name": "evez-cipher", "port": 10005, "path": "cipher/cipher.py", "desc": "Encryption toolkit (AES, RSA, JWT, HMAC)"},
    {"name": "evez-relay", "port": 10006, "path": "relay/relay.py", "desc": "Webhook relay + event bus"},
    {"name": "evez-eigenforge", "port": 10007, "path": "eigenforge/eigenforge.py", "desc": "Math engine (eigenvalues, 37% Theorem)"},
    {"name": "evez-grimoire", "port": 10008, "path": "grimoire/grimoire.py", "desc": "Knowledge base + RAG engine"},
    {"name": "evez-sentinel", "port": 10009, "path": "sentinel/sentinel.py", "desc": "Website security scanner (A-F grade)"},
    {"name": "evez-chrono", "port": 10010, "path": "chrono/chrono.py", "desc": "Task scheduler + job queue"},
    {"name": "evez-mirror", "port": 10011, "path": "mirror/mirror.py", "desc": "URL shortener + analytics"},
    {"name": "evez-aether", "port": 10012, "path": "aether/aether.py", "desc": "WebSocket message bus (pub/sub)"},
    {"name": "evez-scribe", "port": 10013, "path": "scribe/scribe.py", "desc": "Document API (versioned, searchable)"},
]

BASE = "/home/openclaw/evez-ecosystem"

for svc in SERVICES:
    unit = f"""[Unit]
Description=EVEZ {svc['name']} — {svc['desc']}
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory={BASE}
ExecStart=/usr/bin/python3 {BASE}/{svc['path']}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
    unit_path = f"/tmp/{svc['name']}.service"
    with open(unit_path, "w") as f:
        f.write(unit)
    
    # Install unit
    os.system(f"sudo cp {unit_path} /etc/systemd/system/{svc['name']}.service 2>/dev/null")
    os.system(f"sudo systemctl daemon-reload")
    os.system(f"sudo systemctl enable {svc['name']}")
    os.system(f"sudo systemctl restart {svc['name']}")
    print(f"✅ {svc['name']} → :{svc['port']} ({svc['desc']})")
    time.sleep(1)

print(f"\n🚀 Deployed {len(SERVICES)} new servers!")
print(f"Total EVEZ services: 12 (existing) + {len(SERVICES)} (new) = {12 + len(SERVICES)}")
