#!/bin/bash
cd /home/openclaw/evez-ecosystem/evez-dashboard
exec python3 -m http.server 9999 --bind 127.0.0.1
