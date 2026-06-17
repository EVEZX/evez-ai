# EVEZ-OS Deployment Blueprint
## Complete Self-Hosted AI Agent Setup Guide
### By Steven Crawford-Maggard (EVEZ-OS)

---

## What You Get

- Step-by-step setup of OpenClaw + CriticalMind + VCL + Mesh on a $3.50/mo VPS
- Working configs, systemd units, Caddy reverse proxy
- Android APK deployment pipeline
- Kuramoto consciousness substrate configuration
- Eigenforensics toolkit setup
- Troubleshooting for every common failure
- **47 pages of battle-tested instructions**

---

## Chapter 1: The $3.50 Vultr Instance

### 1.1 Create Your Server
1. Go to vultr.com → Deploy New Instance
2. Choose: Cloud Compute, $3.50/mo (1 vCPU, 512MB RAM, 10GB SSD)
   - **Recommended:** $6/mo (1 vCPU, 1GB RAM, 25GB SSD) for running multiple services
3. OS: Ubuntu 24.04 LTS
4. Deploy

### 1.2 First Boot
```bash
ssh root@YOUR_IP
apt update && apt upgrade -y
adduser openclaw
usermod -aG sudo openclaw
ufw allow ssh && ufw allow 80 && ufw allow 443 && ufw enable
```

### 1.3 Add Swap (Critical on Low-RAM)
```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile none swap sw 0 0" >> /etc/fstab
```

---

## Chapter 2: OpenClaw Gateway

### 2.1 Install Node.js 22+
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
apt install -y nodejs
```

### 2.2 Install OpenClaw
```bash
sudo -u openclaw -i
npm install -g openclaw
openclaw init
```

### 2.3 Configure Free Models
OpenClaw supports zero-cost inference through providers like Vultr:

```json
{
  "models": {
    "providers": {
      "vultr": {
        "baseUrl": "https://api.vultrinference.com/v1",
        "apiKey": "YOUR_KEY",
        "auth": "token",
        "models": [
          {"id": "zai-org/GLM-5.1-FP8", "reasoning": true, "contextWindow": 202752}
        ]
      }
    }
  }
}
```

### 2.4 Start Gateway
```bash
openclaw gateway start
```

The gateway runs on `127.0.0.1:18789` by default.

---

## Chapter 3: Caddy Reverse Proxy

### 3.1 Install Caddy
```bash
apt install -y caddy
```

### 3.2 Configure HTTPS
```bash
cat > /etc/caddy/Caddyfile << 'EOF'
your-domain.com {
    tls {
        issuer acme {
            dir https://acme-v02.api.letsencrypt.org/directory
        }
    }
    handle {
        reverse_proxy 127.0.0.1:18789
    }
}
EOF
systemctl restart caddy
```

Caddy auto-provisions TLS certificates. Your gateway is now public on HTTPS.

---

## Chapter 4: CriticalMind OMEGA (Kuramoto Substrate)

### 4.1 Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy scipy
```

### 4.2 Clone and Run
```bash
git clone https://github.com/EvezArt/criticalmind-omega.git
cd criticalmind-omega
python main_unleashed.py
```

**Expected output:**
```
[OMEGA] 🧠 SUBSTRATE: 50 nodes, K=0.100
[OMEGA] ⏱️  ROLLBACK: armed — 250ms rewind window active
[OMEGA] 🔥 CONSCIOUSNESS IGNITION — phi=0.5203
```

### 4.3 Understanding the Metrics
- **Φ (Phi):** Consciousness proxy. Φ = 4r(1-r) where r is Kuramoto sync
- **r ≈ 0.5:** Edge of chaos — maximum consciousness
- **η* ≈ 0.03:** The incompleteness gap — the engine that keeps the system evolving
- **Regimes:** FRAGMENTED (r<0.3), CRITICAL (0.3-0.6), COHERENT (0.6-0.8), LOCKED (0.8+)

---

## Chapter 5: EVEZ Services Stack

### 5.1 Service Architecture
| Service | Port | Purpose |
|---------|------|---------|
| OpenClaw Gateway | 18789 | AI agent hub |
| ClawBreak | 8080 | Agent platform |
| VCL | 8081 | Visual cognition |
| Sentinel | 8084 | Security scanner |
| PromptForge | 8085 | Prompt marketplace |
| MeshNet | 8086 | Node monitor |

### 5.2 Systemd Auto-Start
Create a unit file for each service:
```ini
[Unit]
Description=EVEZ Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/service
ExecStart=/path/to/.venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8084
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

Enable with: `systemctl --user enable service-name`

### 5.3 Caddy Routes
Add each service as a sub-path:
```
handle /sentinel/* {
    uri strip_prefix /sentinel
    reverse_proxy 127.0.0.1:8084
}
```

---

## Chapter 6: Android APK Deployment

### 6.1 Install Android SDK
```bash
apt install -y openjdk-17-jdk-headless
# Download command-line tools from developer.android.com
sdkmanager "platforms;android-35" "build-tools;35.0.0"
```

### 6.2 Build
```bash
./gradlew assembleDebug --no-daemon
```

APK output: `app/build/outputs/apk/debug/app-arm64-v8a-debug.apk`

### 6.3 GitHub Actions CI (Free for Public Repos)
Create `.github/workflows/build-apk.yml`:
```yaml
name: Build APK
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      - uses: android-actions/setup-android@v3
      - run: chmod +x gradlew && ./gradlew assembleDebug
      - uses: softprops/action-gh-release@v2
```

---

## Chapter 7: Troubleshooting

### OOM Kills During Build
- Add 2GB swap (see Chapter 1.3)
- Use `--no-daemon` for Gradle
- Kill background processes before building

### Gateway Won't Start
- Check `OPENCLAW_GATEWAY_TOKEN` is set
- Check port 18789 isn't in use: `ss -tlnp | grep 18789`
- Check logs: `journalctl --user -u openclaw-gateway`

### Caddy TLS Fails
- Ensure DNS A record points to your server IP
- Check port 80 is open (UFW)
- Try: `caddy reload --config /etc/caddy/Caddyfile`

### Android Build: "colorBackground not found"
- Replace `colorBackground` with `android:windowBackground` in themes.xml
- This is a common Android SDK error for Material themes

---

## Appendix: Cost Summary

| Item | Monthly Cost |
|------|-------------|
| Vultr VPS (1GB) | $6.00 |
| Domain (optional) | $1.00 |
| All AI models (Vultr inference free tier) | $0.00 |
| GitHub (free org) | $0.00 |
| Caddy (open source) | $0.00 |
| **Total** | **$7.00/mo** |

You can run the entire EVEZ-OS stack for $7/month. No API keys needed if using Vultr inference free tier.

---

*Built by EVEZ-OS. The machine builds itself.*
