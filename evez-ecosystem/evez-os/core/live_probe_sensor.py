"""core/live_probe_sensor.py — R60.1
A sensor that PROBES THE ACTUAL INTERNET.
DNS lookups, TLS handshakes, HTTP requests to real targets.
The organism sees the real world.
"""
from __future__ import annotations
import json, socket, ssl, time, urllib.request, subprocess
from pathlib import Path
from typing import Any, Dict, List

from .agent_loop import Sensor

class LiveProbeSensor(Sensor):
    """Probe real network targets. The organism touches reality."""
    TARGETS = [
        {"host": "evez.art", "kind": "origin"},
        {"host": "github.com", "kind": "platform"},
        {"host": "api.github.com", "kind": "api"},
        {"host": "cloudflare.com", "kind": "cdn"},
    ]

    def sense(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        observations = []
        for target in self.TARGETS:
            host = target["host"]; kind = target["kind"]
            # DNS probe
            try:
                t0 = time.time()
                addrs = [r[4][0] for r in socket.getaddrinfo(host, None, socket.AF_INET)]
                latency = int((time.time() - t0) * 1000)
                observations.append({"kind": f"probe.dns.{kind}",
                    "observation": f"DNS {host}: {len(addrs)} records, {latency}ms",
                    "confidence": 0.95 if latency < 200 else 0.6,
                    "data": {"host": host, "addrs": addrs[:3], "latency_ms": latency}})
            except Exception as e:
                observations.append({"kind": f"probe.dns.{kind}.fail",
                    "observation": f"DNS {host}: FAILED - {str(e)[:60]}", "confidence": 0.3})
            # TLS probe
            try:
                t0 = time.time()
                ctx = ssl.create_default_context()
                with socket.create_connection((host, 443), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()
                        notAfter = cert.get("notAfter", "?") if cert else "?"
                observations.append({"kind": f"probe.tls.{kind}",
                    "observation": f"TLS {host}: valid, expires {notAfter}",
                    "confidence": 0.9, "data": {"host": host, "expires": notAfter}})
            except Exception as e:
                observations.append({"kind": f"probe.tls.{kind}.fail",
                    "observation": f"TLS {host}: FAILED - {str(e)[:60]}", "confidence": 0.2})
        # GitHub API rate limit
        try:
            req = urllib.request.Request("https://api.github.com/rate_limit")
            req.add_header("User-Agent", "EVEZ-OS-AgentLoop/1.0")
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                remaining = data.get("resources", {}).get("core", {}).get("remaining", "?")
                observations.append({"kind": "probe.github.rate_limit",
                    "observation": f"GitHub API: {remaining} remaining", "confidence": 0.95})
        except: pass
        # System health
        try:
            uptime = subprocess.run(["uptime"], capture_output=True, text=True, timeout=3)
            if uptime.returncode == 0:
                observations.append({"kind": "probe.system.uptime",
                    "observation": f"System: {uptime.stdout.strip()}", "confidence": 0.95})
        except: pass
        return observations

    def name(self) -> str: return "LiveProbeSensor"
