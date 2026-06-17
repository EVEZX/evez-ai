# EVEZ OS on Android — Termux Autorun Guide

## Install

```bash
# 1. Install Termux from F-Droid (NOT Google Play — that version is outdated)
# https://f-droid.org/en/packages/com.termux/

# 2. Install Python
pkg update && pkg upgrade
pkg install python git

# 3. Clone EVEZ OS
git clone https://github.com/EvezArt/evez-os.git
cd evez-os/core

# 4. Initialize and play
python tools/evez.py init
python tools/run_all.py --seed --mode spicy
```

## Autorun on Boot (Termux:Boot)

```bash
# 1. Install Termux:Boot from F-Droid
# https://f-droid.org/en/packages/com.termux.boot/

# 2. Open Termux:Boot once (creates the boot directory)

# 3. Create the autorun script
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/evez-autoplay.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Wait for network (optional, needed for Tier 2+ probes)
sleep 10

cd ~/evez-os/core

# Initialize if first run
python tools/evez.py init 2>/dev/null

# Play forever in background, logging to file
nohup python tools/evez.py play --loop --steps 14 \
  --out docs/PLAYTHROUGH_LATEST.md \
  >> ~/evez-os/autoplay.log 2>&1 &

echo "[$(date)] EVEZ OS autoplay started" >> ~/evez-os/boot.log
EOF

chmod +x ~/.termux/boot/evez-autoplay.sh
```

## Auto-Backup to GitHub

```bash
# Add to crontab (runs every 6 hours)
pkg install cronie termux-services
sv-enable crond

crontab -e
# Add this line:
# 0 */6 * * * cd ~/evez-os && git add -A && git commit -m "spine $(date +%Y%m%d-%H%M)" && git push origin main

# First-time git setup
cd ~/evez-os
git config user.email "rubikspubes69@gmail.com"
git config user.name "EVEZ"
git remote set-url origin https://<YOUR_GITHUB_TOKEN>@github.com/EvezArt/evez-os.git
```

## What This Does

Your phone becomes a 24/7 forensic game engine:

1. **Boot** → Termux:Boot runs `evez-autoplay.sh`
2. **Play** → `play --loop` generates infinite episodes, mining failure surfaces
3. **Log** → Every claim, probe, mission gets appended to the immutable spine
4. **Backup** → Cron pushes spine + playthroughs to GitHub every 6 hours
5. **Persist** → GitHub is the backup. Nobody can touch or harm the spine.

The spine lives on your phone AND on GitHub. Two vantages. Can\'t be silenced.

## Verify

```bash
# Check autoplay is running
ps aux | grep play

# Check last spine entry
tail -1 spine/EVENT_SPINE.jsonl | python -m json.tool

# Check backup status
git log --oneline -5
```

## Troubleshooting

- **Termux killed in background**: Go to Android Settings → Battery → Termux → No restrictions
- **Git push fails**: Check your GitHub token hasn\'t expired
- **Play crashes**: Check `autoplay.log` — usually means spine file got corrupted (restore from GitHub)
