"""core/route_opt.py — Route Optimizer
EVEZ OS v1.1.0+

Measures and ranks routing candidates (DNS resolvers, TCP hosts, HTTP URLs)
from a given vantage using conservative scoring:

    score = (p95_latency_ms, loss_rate, median_latency_ms)

Prefers consistent low jitter (p95) over a lucky fast ping.
Appends append-only snapshot to spine/EVENT_SPINE.jsonl when --append-spine is set.

Usage (standalone):
    python3 core/route_opt.py --mode full --trials 12 --timeout 2 --append-spine

Usage (via evez.py):
    python3 tools/evez.py route-opt -- --mode full --trials 12 --append-spine

Multi-vantage aggregation:
    Run with different EVEZ_VANTAGE on each machine, merge spine files,
    then run tools/route_agg.py to find best vantage per target.
"""

import argparse
import json
import math
import os
import socket
import statistics
import subprocess
import time
import datetime
from datetime import timezone
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_DNS_RESOLVERS = [
    "8.8.8.8",        # Google
    "1.1.1.1",        # Cloudflare
    "9.9.9.9",        # Quad9
    "208.67.222.222", # OpenDNS
]

DEFAULT_TCP_HOSTS = [
    "github.com",
    "gumroad.com",
    "moltbook.com",
    "openclaw.ai",
]

DEFAULT_HTTP_URLS = [
    "https://github.com",
    "https://gumroad.com",
    "https://moltbook.com",
    "https://openclaw.ai",
]

DEFAULT_DNS_QUERY = "github.com"

SPINE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "spine", "EVENT_SPINE.jsonl"
)


# ── Scoring ───────────────────────────────────────────────────────────────────

def score(candidate: dict) -> tuple:
    """Conservative score: (p95_ms, loss_rate, median_ms)."""
    return (
        candidate.get("p95_ms", 1e9),
        candidate.get("loss_rate", 1.0),
        candidate.get("median_ms", 1e9),
    )


# ── Probes ────────────────────────────────────────────────────────────────────

def probe_dns(resolver: str, query: str, trials: int, timeout: float) -> dict:
    """Measure DNS resolution latency using dig (if available) or socket fallback."""
    latencies = []
    errors = 0

    has_dig = subprocess.run(
        ["which", "dig"], capture_output=True
    ).returncode == 0

    for _ in range(trials):
        t0 = time.perf_counter()
        if has_dig:
            try:
                result = subprocess.run(
                    ["dig", f"@{resolver}", query, "+time=2", "+tries=1",
                     "+noall", "+answer"],
                    capture_output=True, timeout=timeout + 1
                )
                elapsed = (time.perf_counter() - t0) * 1000
                if result.returncode == 0 and result.stdout:
                    latencies.append(elapsed)
                else:
                    errors += 1
            except Exception:
                errors += 1
        else:
            try:
                socket.setdefaulttimeout(timeout)
                socket.getaddrinfo(query, None)
                elapsed = (time.perf_counter() - t0) * 1000
                latencies.append(elapsed)
            except Exception:
                errors += 1

    n = len(latencies)
    loss_rate = errors / trials if trials > 0 else 1.0

    if n == 0:
        return {
            "name": resolver, "kind": "dns",
            "p95_ms": 1e9, "median_ms": 1e9, "mean_ms": 1e9,
            "loss_rate": loss_rate, "trials": trials,
            "dig_available": has_dig, "error": "all_trials_failed",
        }

    sorted_lat = sorted(latencies)
    p95_idx = max(0, int(math.ceil(0.95 * n)) - 1)
    return {
        "name": resolver, "kind": "dns",
        "p95_ms": round(sorted_lat[p95_idx], 2),
        "median_ms": round(statistics.median(latencies), 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "loss_rate": round(loss_rate, 4),
        "trials": trials, "dig_available": has_dig,
    }


def probe_tcp(host: str, port: int, trials: int, timeout: float) -> dict:
    """Measure TCP connect latency."""
    latencies = []
    errors = 0
    for _ in range(trials):
        t0 = time.perf_counter()
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception:
            errors += 1

    n = len(latencies)
    loss_rate = errors / trials if trials > 0 else 1.0
    if n == 0:
        return {
            "name": f"{host}:{port}", "kind": "tcp",
            "p95_ms": 1e9, "median_ms": 1e9, "mean_ms": 1e9,
            "loss_rate": loss_rate, "trials": trials, "error": "all_trials_failed",
        }

    sorted_lat = sorted(latencies)
    p95_idx = max(0, int(math.ceil(0.95 * n)) - 1)
    return {
        "name": f"{host}:{port}", "kind": "tcp",
        "p95_ms": round(sorted_lat[p95_idx], 2),
        "median_ms": round(statistics.median(latencies), 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "loss_rate": round(loss_rate, 4),
        "trials": trials,
    }


def probe_http(url: str, trials: int, timeout: float) -> dict:
    """Measure HTTP HEAD latency."""
    import urllib.request
    latencies = []
    errors = 0
    for _ in range(trials):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "EVEZ-RouteOpt/1.0")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp.read()
            latencies.append((time.perf_counter() - t0) * 1000)
        except Exception:
            errors += 1

    n = len(latencies)
    loss_rate = errors / trials if trials > 0 else 1.0
    if n == 0:
        return {
            "name": url, "kind": "http",
            "p95_ms": 1e9, "median_ms": 1e9, "mean_ms": 1e9,
            "loss_rate": loss_rate, "trials": trials, "error": "all_trials_failed",
        }

    sorted_lat = sorted(latencies)
    p95_idx = max(0, int(math.ceil(0.95 * n)) - 1)
    return {
        "name": url, "kind": "http",
        "p95_ms": round(sorted_lat[p95_idx], 2),
        "median_ms": round(statistics.median(latencies), 2),
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "loss_rate": round(loss_rate, 4),
        "trials": trials,
    }


# ── Runner ────────────────────────────────────────────────────────────────────

def run_route_opt(
    mode: str = "full",
    dns_resolvers: Optional[list] = None,
    hosts: Optional[list] = None,
    port: int = 443,
    urls: Optional[list] = None,
    trials: int = 12,
    timeout: float = 2.0,
    append_spine: bool = False,
    vantage_id: Optional[str] = None,
    quiet: bool = False,
) -> dict:
    vantage = vantage_id or os.environ.get("EVEZ_VANTAGE", socket.gethostname())
    results = {}

    if mode in ("dns", "full"):
        resolvers = dns_resolvers or DEFAULT_DNS_RESOLVERS
        dns_results = [probe_dns(r, DEFAULT_DNS_QUERY, trials, timeout)
                       for r in resolvers]
        dns_results.sort(key=score)
        results["dns"] = dns_results

    if mode in ("tcp", "full"):
        tcp_hosts = hosts or DEFAULT_TCP_HOSTS
        tcp_results = [probe_tcp(h, port, trials, timeout) for h in tcp_hosts]
        tcp_results.sort(key=score)
        results["tcp"] = tcp_results

    if mode in ("http", "full"):
        http_urls = urls or DEFAULT_HTTP_URLS
        http_results = [probe_http(u, trials, timeout) for u in http_urls]
        http_results.sort(key=score)
        results["http"] = http_results

    snapshot = {
        "kind": "route.snapshot",
        "vantage_id": vantage,
        "timestamp": datetime.datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "trials": trials,
        "timeout_s": timeout,
        "results": results,
    }

    if not quiet:
        _print_report(snapshot)

    if append_spine:
        _append_to_spine(snapshot)

    return snapshot


def _print_report(snapshot: dict) -> None:
    print(f"\n=== Route Optimizer Report ===")
    print(f"Vantage : {snapshot['vantage_id']}")
    print(f"Time    : {snapshot['timestamp']}")
    print(f"Mode    : {snapshot['mode']} | Trials: {snapshot['trials']} | Timeout: {snapshot['timeout_s']}s\n")
    for section, rows in snapshot.get("results", {}).items():
        print(f"\u2500\u2500 {section.upper()} \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
        print(f"  {'Name':<40} {'p95':>8}ms  {'loss':>6}  {'med':>8}ms")
        print(f"  {'-'*40} {'-'*8}   {'-'*6}  {'-'*8}")
        for c in rows:
            p95 = c.get("p95_ms", 1e9)
            loss = c.get("loss_rate", 1.0)
            med = c.get("median_ms", 1e9)
            err = " \u2190 ERROR" if c.get("error") else ""
            p95_str = f"{p95:8.1f}" if p95 < 1e8 else "  TIMEOUT"
            med_str = f"{med:8.1f}" if med < 1e8 else "  TIMEOUT"
            print(f"  {c['name']:<40} {p95_str}   {loss:6.4f}  {med_str}{err}")
        print()


def _append_to_spine(snapshot: dict) -> None:
    import hashlib
    spine_dir = os.path.dirname(SPINE_PATH)
    os.makedirs(spine_dir, exist_ok=True)
    raw = json.dumps(
        {k: v for k, v in snapshot.items() if k != "hash"}, sort_keys=True
    )
    snapshot["hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]
    with open(SPINE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")
    print(f"[spine] Appended route.snapshot \u2192 {SPINE_PATH}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EVEZ Route Optimizer \u2014 rank routing candidates by conservative latency score"
    )
    parser.add_argument("--mode", choices=["dns", "tcp", "http", "full"], default="full")
    parser.add_argument("--resolvers", type=str, help="Comma-separated DNS resolvers")
    parser.add_argument("--hosts", type=str, help="Comma-separated TCP hosts")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--urls", type=str, help="Comma-separated HTTP URLs")
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--append-spine", action="store_true")
    parser.add_argument("--vantage", type=str)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run_route_opt(
        mode=args.mode,
        dns_resolvers=args.resolvers.split(",") if args.resolvers else None,
        hosts=args.hosts.split(",") if args.hosts else None,
        port=args.port,
        urls=args.urls.split(",") if args.urls else None,
        trials=args.trials,
        timeout=args.timeout,
        append_spine=args.append_spine,
        vantage_id=args.vantage,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
