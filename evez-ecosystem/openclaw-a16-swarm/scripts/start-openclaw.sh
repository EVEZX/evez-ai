#!/data/data/com.termux/files/usr/bin/bash
# EVEZ A16 — Start OpenClaw as background service
# Run from Termux. Keeps running even when screen off.

echo "🦞 Starting OpenClaw gateway..."

# Use proot to run in Ubuntu
proot-distro login ubuntu -- bash -c '
    # Kill any existing gateway
    pkill -f "openclaw gateway" 2>/dev/null || true
    sleep 1
    
    # Start gateway in background
    nohup openclaw gateway start > /home/openclaw/openclaw.log 2>&1 &
    echo $! > /home/openclaw/openclaw.pid
    
    # Wait for startup
    sleep 5
    
    if kill -0 $(cat /home/openclaw/openclaw.pid) 2>/dev/null; then
        echo "✅ OpenClaw running (PID: $(cat /home/openclaw/openclaw.pid))"
        echo "   Logs: tail -f /home/openclaw/openclaw.log"
        echo "   Stop: kill $(cat /home/openclaw/openclaw.pid)"
    else
        echo "❌ Failed to start. Check logs."
        cat /home/openclaw/openclaw.log | tail -20
    fi
'
