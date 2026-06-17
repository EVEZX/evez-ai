#!/bin/bash
# EVEZ-OS — Run forever with auto-restart
cd /home/openclaw/.openclaw/workspace/evez-os-sensors
export PYTHONPATH=/home/openclaw/.openclaw/workspace/evez-os-sensors
while true; do
    echo "[$(date)] EVEZ-OS starting..." >> /tmp/evez-os-forever.log
    /usr/bin/python3 autonomous_daemon.py --interval 60 2>&1 | tee -a /tmp/evez-os-forever.log
    echo "[$(date)] EVEZ-OS crashed, restarting in 30s..." >> /tmp/evez-os-forever.log
    sleep 30
done
