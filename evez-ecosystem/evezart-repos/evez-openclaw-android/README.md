# EvezArt OpenClaw Android

Kotlin Android client for the OpenClaw / EVEZ-OS stack. WebView-based — load any OpenClaw web UI (local Termux tunnel or remote).

## Get the APK

**GitHub Actions builds it automatically on every push to `main`.**

1. Go to [Actions](https://github.com/EvezArt/evez-openclaw-android/actions)
2. Click the latest **Build Android APK** run
3. Download `evez-openclaw-debug` artifact (signed with debug key, install directly)

Or download from [Releases](https://github.com/EvezArt/evez-openclaw-android/releases).

## Build locally (Android Studio)

```bash
git clone https://github.com/EvezArt/evez-openclaw-android
cd evez-openclaw-android
./gradlew assembleDebug
# APK at: app/build/outputs/apk/debug/app-debug.apk
```

## Build locally (Termux on Android)

```bash
pkg install openjdk-17
git clone https://github.com/EvezArt/evez-openclaw-android
cd evez-openclaw-android
export ANDROID_HOME=$PREFIX
./gradlew assembleDebug
```

## Point at your OpenClaw instance

Launch with intent:
```bash
adb shell am start -n io.evezart.openclaw/.MainActivity \
  --es OPENCLAW_URL http://localhost:3000
```

Or edit `MainActivity.kt` and change the default URL.

## Requirements

- Android 8.0+ (API 26)
- Internet permission
- `android:usesCleartextTraffic=true` enabled for localhost access
