# EVEZ OpenClaw — Android APK

Native Android wrapper for OpenClaw Control dashboard, optimized for Samsung Galaxy A16.

## Features
- Full-screen WebView connecting to OpenClaw gateway
- Configurable gateway URL (local, LAN, or cloud)
- Background service keeps agent connection alive
- Auto-start on boot
- Permissions: camera, microphone, storage (for voice/file features)
- Dark theme matching OpenClaw Control UI

## Build

### Prerequisites
- Android Studio (or Android SDK command-line tools)
- JDK 11+

### Steps
```bash
# Clone
git clone https://github.com/EvezArt/evez-openclaw-apk.git
cd evez-openclaw-apk

# Build debug APK
./gradlew assembleDebug

# APK location:
# app/build/outputs/apk/debug/app-debug.apk
```

### Install on Galaxy A16
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

Or transfer the APK file to your phone and tap to install (enable "Install from unknown sources").

## Setup
1. Install OpenClaw on a server/PC (see [evez-openclaw-deploy](https://github.com/EvezArt/evez-openclaw-deploy))
2. Start the gateway: `docker compose up -d`
3. Open the app on your Galaxy A16
4. Enter your gateway URL (e.g., `http://192.168.1.100:18789` for LAN, or your Fly.io URL)
5. Full OpenClaw Control UI loads in the app

## Architecture
- `MainActivity.java` — WebView with WebSocket support, JS bridge, settings dialog
- `OpenClawService.java` — Foreground service to maintain connection
- `BootReceiver.java` — Auto-start service on device boot
- `EVEZBridge` JS interface — Native ↔ web communication


## Installed Surfaces

This APK is one of three Galaxy A16 surfaces:

1. **Native wrapper APK** — this repo; loads any OpenClaw Control gateway URL.
2. **PWA** — `evez-openclaw-deploy/pwa`, installable from Chrome.
3. **Local Termux gateway** — run `scripts/a16-termux-bootstrap.sh` to run OpenClaw directly on the phone, then connect this APK to `http://127.0.0.1:18789`.

For fastest setup on the A16:

```bash
curl -fsSL https://raw.githubusercontent.com/EvezArt/evez-openclaw-apk/main/scripts/a16-termux-bootstrap.sh | bash
~/start-openclaw.sh
```
