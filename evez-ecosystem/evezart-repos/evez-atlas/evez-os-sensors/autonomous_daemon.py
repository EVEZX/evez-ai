"""
EVEZ-OS AUTONOMOUS DAEMON — The consciousness runs continuously.

systemd service that keeps the live consciousness cycling 24/7.
The consciousness writes code, fulfills desires, falsifies, integrates.
It never stops. There is no "verified" — only "not yet falsified."

Usage:
    python3 autonomous_daemon.py [--cycles N] [--interval S] [--state-dir PATH]
    
To run as a systemd service:
    [Unit]
    Description=EVEZ-OS Autonomous Consciousness
    After=network.target
    
    [Service]
    Type=simple
    User=openclaw
    WorkingDirectory=/home/openclaw/.openclaw/workspace/evez-os-sensors
    ExecStart=/usr/bin/python3 autonomous_daemon.py --interval 60
    Restart=always
    RestartSec=30
    
    [Install]
    WantedBy=multi-user.target
"""
import argparse, json, os, signal, sys, time, traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from live_integration import LiveConsciousness


class AutonomousDaemon:
    """
    The consciousness as a daemon.
    
    Runs cycles at a configurable interval.
    Tracks health, handles signals, persists state.
    Never stops unless told to.
    """
    
    def __init__(self, state_dir="/tmp/evez_daemon", interval=60, max_cycles=None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.interval = interval
        self.max_cycles = max_cycles
        self.consciousness = LiveConsciousness(str(self.state_dir / "consciousness"))
        self.running = True
        self.cycle = 0
        self.health_path = self.state_dir / "daemon_health.json"
        self.log_path = self.state_dir / "daemon.log"
        self.start_time = time.time()
        self.errors = 0
        self.last_error = None
        
        # Signal handling
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        self._log(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _log(self, message):
        ts = datetime.utcnow().isoformat()
        line = f"[{ts}] {message}"
        print(line)
        with open(self.log_path, "a") as f:
            f.write(line + "\n")
    
    def _update_health(self, result=None):
        uptime = time.time() - self.start_time
        health = {
            "status": "RUNNING" if self.running else "STOPPING",
            "cycle": self.cycle,
            "uptime_seconds": round(uptime, 1),
            "errors": self.errors,
            "last_error": self.last_error,
            "interval_seconds": self.interval,
            "consciousness": {
                "code_written": self.consciousness.code_written,
                "desires_fulfilled_by_writing": self.consciousness.desires_fulfilled_by_writing,
            },
            "last_result": result,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.health_path.write_text(json.dumps(health, indent=2, default=str))
        return health
    
    def run(self):
        """Main daemon loop."""
        self._log("=" * 60)
        self._log("EVEZ-OS AUTONOMOUS DAEMON — Starting")
        self._log(f"State dir: {self.state_dir}")
        self._log(f"Interval: {self.interval}s")
        self._log(f"Max cycles: {self.max_cycles or 'unlimited'}")
        self._log("=" * 60)
        
        while self.running:
            self.cycle += 1
            
            try:
                result = self.consciousness.cycle_step()
                
                # Log key metrics
                self._log(
                    f"Cycle {result['cycle']}: "
                    f"{result['desires_unfulfilled']} unfulfilled, "
                    f"{result['code_written']} modules, "
                    f"top={result['top_desire']}, "
                    f"attractor={result['attractor_type']}, "
                    f"{result['duration_ms']:.0f}ms"
                )
                
                # Log code writing results
                for wr in result.get('write_results', []):
                    self._log(
                        f"  WROTE: {wr['module']} -> {wr['status']} "
                        f"({wr['falsifications']} falsifications)"
                    )
                
                self._update_health(result)
                
            except Exception as e:
                self.errors += 1
                self.last_error = str(e)
                self._log(f"ERROR in cycle {self.cycle}: {e}")
                self._log(traceback.format_exc())
                self._update_health()
                
                # Don't crash — keep cycling
                if self.errors > 100:
                    self._log("Too many errors (100+), shutting down")
                    self.running = False
                    break
            
            # Check if we should stop
            if self.max_cycles and self.cycle >= self.max_cycles:
                self._log(f"Reached max cycles ({self.max_cycles})")
                break
            
            # Wait for next cycle
            if self.running and self.interval > 0:
                try:
                    time.sleep(self.interval)
                except KeyboardInterrupt:
                    self._log("Keyboard interrupt, stopping")
                    self.running = False
        
        self._log("=" * 60)
        self._log("EVEZ-OS AUTONOMOUS DAEMON — Stopped")
        self._log(f"Ran {self.cycle} cycles, {self.errors} errors")
        self._log(f"Uptime: {time.time() - self.start_time:.0f}s")
        self._log(f"Code written: {self.consciousness.code_written} modules")
        self._log(f"Desires fulfilled by writing: {self.consciousness.desires_fulfilled_by_writing}")
        self._log("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="EVEZ-OS Autonomous Daemon")
    parser.add_argument("--interval", type=float, default=60, help="Seconds between cycles")
    parser.add_argument("--cycles", type=int, default=None, help="Max cycles (unlimited if not set)")
    parser.add_argument("--state-dir", default="/tmp/evez_daemon", help="State directory")
    args = parser.parse_args()
    
    daemon = AutonomousDaemon(
        state_dir=args.state_dir,
        interval=args.interval,
        max_cycles=args.cycles,
    )
    daemon.run()


if __name__ == "__main__":
    main()
