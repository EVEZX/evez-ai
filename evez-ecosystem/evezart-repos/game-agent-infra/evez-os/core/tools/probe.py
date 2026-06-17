#!/usr/bin/env python3
"""
Probe tools (Tier 2/3)

Single-vantage probes (local):
  - dns: resolve A/AAAA via dig if available, else socket.getaddrinfo
  - http: fetch URL, record status, headers, latency
  - tls: fetch leaf cert + issuer + validity dates
  - ping: ICMP ping (if available) else TCP connect timing

All probes can append an immutable event into spine/EVENT_SPINE.jsonl.

Security posture:
  - Read-only network diagnostics.
  - No exploitation, no scanning beyond explicit targets the operator supplies.
"""
from __future__ import annotations
import datetime, json, os, shutil, socket, ssl, subprocess, time, urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"

def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat() + "Z"

def _append_spine(event: Dict[str, Any]) -> None:
    SPINE.parent.mkdir(parents=True, exist_ok=True)
    with SPINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def _dig_available() -> bool:
    return shutil.which("dig") is not None

def _ping_available() -> bool:
    return shutil.which("ping") is not None

def probe_dns(name: str, rrtype: str = "A", resolver: Optional[str] = None, timeout_s: int = 5) -> Dict[str, Any]:
    t0 = time.time()
    answers: List[str] = []
    method = "socket"
    raw = ""
    if _dig_available():
        method = "dig"
        cmd = ["dig", "+time=%d" % max(1, timeout_s), "+tries=1", "+short", name, rrtype]
        if resolver:
            cmd.insert(1, "@"+resolver)
        p = subprocess.run(cmd, capture_output=True, text=True)
        raw = (p.stdout or "") + (p.stderr or "")
        answers = [ln.strip() for ln in (p.stdout or "").splitlines() if ln.strip()]
    else:
        family = socket.AF_INET if rrtype.upper() == "A" else socket.AF_INET6
        try:
            info = socket.getaddrinfo(name, None, family=family, type=socket.SOCK_STREAM)
            for item in info:
                addr = item[4][0]
                if addr not in answers:
                    answers.append(addr)
        except Exception as e:
            raw = repr(e)

    dt_ms = int((time.time() - t0) * 1000)
    return {
        "kind": "probe.dns",
        "ts": _utcnow(),
        "target": {"name": name, "rrtype": rrtype.upper(), "resolver": resolver},
        "method": method,
        "answers": answers,
        "latency_ms": dt_ms,
        "raw": raw[:4000],
    }

def probe_http(url: str, method: str = "GET", timeout_s: int = 10, headers: Optional[Dict[str,str]] = None) -> Dict[str, Any]:
    t0 = time.time()
    req = urllib.request.Request(url, method=method.upper(), headers=headers or {})
    status = None
    resp_headers: Dict[str,str] = {}
    body_sample = ""
    err = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            status = getattr(r, "status", None)
            resp_headers = {k: v for (k, v) in r.headers.items()}
            body = r.read(2048)
            try:
                body_sample = body.decode("utf-8", errors="replace")
            except Exception:
                body_sample = repr(body)
    except Exception as e:
        err = repr(e)

    dt_ms = int((time.time() - t0) * 1000)
    return {
        "kind": "probe.http",
        "ts": _utcnow(),
        "target": {"url": url, "method": method.upper()},
        "status": status,
        "headers": resp_headers,
        "latency_ms": dt_ms,
        "body_sample": body_sample[:2000],
        "error": err[:2000],
    }

def probe_tls(host: str, port: int = 443, server_name: Optional[str] = None, timeout_s: int = 6) -> Dict[str, Any]:
    t0 = time.time()
    server_name = server_name or host
    cert = {}
    err = ""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout_s) as sock:
            with ctx.wrap_socket(sock, server_hostname=server_name) as ssock:
                der = ssock.getpeercert(binary_form=True)
                parsed = ssock.getpeercert()
                cert = {
                    "subject": parsed.get("subject"),
                    "issuer": parsed.get("issuer"),
                    "notBefore": parsed.get("notBefore"),
                    "notAfter": parsed.get("notAfter"),
                    "serialNumber": parsed.get("serialNumber"),
                    "version": parsed.get("version"),
                    "subjectAltName": parsed.get("subjectAltName"),
                    "cipher": ssock.cipher(),
                    "tls_version": ssock.version(),
                    "der_sha256": __import__("hashlib").sha256(der).hexdigest() if der else None,
                }
    except Exception as e:
        err = repr(e)

    dt_ms = int((time.time() - t0) * 1000)
    return {
        "kind": "probe.tls",
        "ts": _utcnow(),
        "target": {"host": host, "port": port, "server_name": server_name},
        "cert": cert,
        "latency_ms": dt_ms,
        "error": err[:2000],
    }

def probe_ping(host: str, count: int = 1, timeout_s: int = 2) -> Dict[str, Any]:
    t0 = time.time()
    method = "tcp"
    raw = ""
    ok = False
    if _ping_available():
        method = "ping"
        cmd = ["ping", "-c", str(count), "-W", str(timeout_s), host]
        p = subprocess.run(cmd, capture_output=True, text=True)
        raw = (p.stdout or "") + (p.stderr or "")
        ok = (p.returncode == 0)
    else:
        # TCP connect timing (best-effort)
        try:
            with socket.create_connection((host, 443), timeout=timeout_s):
                ok = True
        except Exception as e:
            raw = repr(e)

    dt_ms = int((time.time() - t0) * 1000)
    return {
        "kind": "probe.ping",
        "ts": _utcnow(),
        "target": {"host": host, "count": count},
        "method": method,
        "ok": ok,
        "latency_ms": dt_ms,
        "raw": raw[:4000],
    }

def run_and_maybe_append(event: Dict[str, Any], append_spine: bool) -> Dict[str, Any]:
    # Tag a vantage (operator/location) so multi-vantage disagreement detection can work.
    # You can set EVEZ_VANTAGE (env) or pass --vantage from the CLI (wired in tools/evez.py).
    if "vantage_id" not in event:
        v = os.environ.get("EVEZ_VANTAGE")
        if v:
            event["vantage_id"] = v
    if append_spine:
        _append_spine(event)
    return event
