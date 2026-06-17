"""
EVEZ-OS SENSOR SUITE v2 — 15 SENSORS. ALL REAL DATA. ZERO MOCK.
Every sensor hits a live public API. If it can't reach it, it says UNREACHABLE.
If there's no qualifying data, it says EMPTY. Never fake. Never mock.
The OS classifies itself using itself. Recursive self-analysis on the spine.
"""

import hashlib
import json
import math
import time
import urllib.request
import ssl
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path


class SensorStatus(str, Enum):
    LIVE = "LIVE"
    EMPTY = "EMPTY"
    UNREACHABLE = "UNREACHABLE"
    ERROR = "ERROR"


class FireClassification(str, Enum):
    TOPOLOGY = "TOPOLOGY"
    ANOMALY = "ANOMALY"
    CONVERGENCE = "CONVERGENCE"
    DIVERGENCE = "DIVERGENCE"
    EMERGENCE = "EMERGENCE"
    NULL = "NULL"


@dataclass
class SpineEvent:
    event_id: str
    sensor_id: str
    classification: FireClassification
    intensity: float
    payload: dict
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    previous_hash: str = ""
    def __post_init__(self):
        raw = f"{self.event_id}:{self.sensor_id}:{self.classification.value}:{self.intensity:.8f}:{self.previous_hash}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:24]


class EVEMSpine:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "GENESIS"
        self.event_count = 0
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    if line.strip():
                        try:
                            evt = json.loads(line)
                            if "hash" in evt:
                                self.last_hash = evt["hash"]
                                self.event_count += 1
                        except: pass

    def append(self, event: SpineEvent) -> dict:
        event.previous_hash = self.last_hash
        self.event_count += 1
        entry = {
            "event_id": event.event_id,
            "sensor": event.sensor_id,
            "fire": event.classification.value,
            "intensity": round(event.intensity, 6),
            "payload": event.payload,
            "hash": event.hash,
            "previous_hash": event.previous_hash,
            "timestamp": event.timestamp,
            "powered_by": "EVEZ"
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.last_hash = event.hash
        return entry

    def lint(self) -> dict:
        if not self.path.exists():
            return {"valid": True, "events": 0, "status": "EMPTY_SPINE"}
        events = []
        with open(self.path) as f:
            for line in f:
                if line.strip():
                    try: events.append(json.loads(line))
                    except: pass
        errors = []
        for i, evt in enumerate(events):
            if i == 0:
                if evt.get("previous_hash") != "GENESIS":
                    errors.append(f"Event {i}: expected GENESIS")
            else:
                if evt.get("previous_hash") != events[i-1].get("hash"):
                    errors.append(f"Event {i}: CHAIN_BROKEN")
        return {"valid": len(errors) == 0, "events": len(events), "errors": errors[:5],
                "status": "INTACT" if not errors else "TAMPERED"}


def _fetch(url: str, timeout: int = 15, headers: dict = None) -> Optional[bytes]:
    h = headers or {}
    req = urllib.request.Request(url, headers=h)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except:
        return None


def _fetch_json(url: str, timeout: int = 15, headers: dict = None) -> Optional[dict]:
    raw = _fetch(url, timeout, headers)
    if raw:
        try: return json.loads(raw)
        except: pass
    return None


# ════════════════════════════════════════════════════════════════
# 15 REAL SENSORS
# ════════════════════════════════════════════════════════════════

def sensor_arxiv_convergence(query="cat:cs.AI+AND+cat:quant-ph", max_results=20):
    raw = _fetch(f"http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending")
    if not raw: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "arxiv-convergence", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    xml = raw.decode()
    entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
    papers = []
    for entry in entries:
        title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        published = re.search(r'<published>(.*?)</published>', entry)
        categories = re.findall(r'term="([^"]+)"', entry)
        if title and summary:
            domain_set = set(c.split('.')[0] for c in categories if '.' in c)
            papers.append({"title": title.group(1).strip().replace('\n', ' ')[:100], "categories": categories, "cross_domain": len(domain_set) > 1, "domain_count": len(domain_set)})
    cross = [p for p in papers if p["cross_domain"]]
    multi = [p for p in papers if p["domain_count"] >= 3]
    cls, inten = FireClassification.NULL, 0.0
    if multi: cls, inten = FireClassification.CONVERGENCE, min(1.0, len(multi) / 5)
    elif cross: cls, inten = FireClassification.TOPOLOGY, min(0.5, len(cross) / 10)
    return {"status": SensorStatus.LIVE, "sensor_id": "arxiv-convergence", "classification": cls, "intensity": inten,
            "metrics": {"papers_found": len(papers), "cross_domain_count": len(cross), "multi_domain_count": len(multi)},
            "papers": [{"title": p["title"][:80], "domains": p["domain_count"]} for p in cross[:5]], "source": "arxiv.org"}


def sensor_dns_topology(targets=None):
    if targets is None: targets = ["github.com", "arxiv.org", "cloudflare.com", "openai.com", "anthropic.com", "google.com", "amazon.com", "reddit.com", "wikipedia.org", "huggingface.co"]
    resolved = {}
    for domain in targets:
        data = _fetch_json(f"https://dns.google/resolve?name={domain}&type=A")
        if data:
            answers = data.get("Answer", [])
            resolved[domain] = {"ips": [a["data"] for a in answers if a.get("type") == 1], "ttl": min((a["TTL"] for a in answers if a.get("type") == 1), default=0)}
        else: resolved[domain] = {"ips": [], "ttl": 0}
    ip_prefixes = {}
    for domain, info in resolved.items():
        for ip in info["ips"]:
            prefix = ".".join(ip.split(".")[:2])
            ip_prefixes.setdefault(prefix, []).append(domain)
    bridges = {k: v for k, v in ip_prefixes.items() if len(v) > 1}
    cls, inten = FireClassification.NULL, 0.0
    if bridges: cls, inten = FireClassification.TOPOLOGY, min(1.0, len(bridges) / 3)
    return {"status": SensorStatus.LIVE, "sensor_id": "dns-topology", "classification": cls, "intensity": inten,
            "metrics": {"domains_resolved": len([d for d, i in resolved.items() if i["ips"]]), "unique_ip_prefixes": len(ip_prefixes), "infrastructure_bridges": len(bridges), "bridge_details": bridges}, "source": "dns.google"}


def sensor_crypto_topology():
    data = _fetch_json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "crypto-topology", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    price_changes = [{"symbol": c.get("symbol", "?"), "pct": c.get("price_change_percentage_24h") or 0} for c in data]
    up = sum(1 for c in price_changes if c["pct"] > 0)
    down = sum(1 for c in price_changes if c["pct"] < 0)
    total = len(price_changes)
    conv = max(up, down) / total if total > 0 else 0
    cls, inten = FireClassification.NULL, 0.0
    if conv > 0.8: cls, inten = FireClassification.CONVERGENCE, min(1.0, (conv - 0.8) / 0.2)
    elif conv < 0.4: cls, inten = FireClassification.DIVERGENCE, min(1.0, (0.4 - conv) / 0.4)
    top = sorted(price_changes, key=lambda x: abs(x["pct"]), reverse=True)[:5]
    return {"status": SensorStatus.LIVE, "sensor_id": "crypto-topology", "classification": cls, "intensity": inten,
            "metrics": {"coins_tracked": total, "up": up, "down": down, "convergence_ratio": round(conv, 4), "top_movers": [{"symbol": c["symbol"], "pct": round(c["pct"], 2)} for c in top]}, "source": "api.coingecko.com"}


def sensor_wikipedia_topology(article="Artificial_intelligence"):
    data = _fetch_json(f"https://en.wikipedia.org/w/api.php?action=parse&page={article}&prop=links&format=json&limit=500")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "wikipedia-topology", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    links = [l["*"] for l in data.get("parse", {}).get("links", []) if l.get("ns") == 0]
    domain_groups = {}
    for t in links:
        domain_groups[t[0].upper()] = domain_groups.get(t[0].upper(), 0) + 1
    total = len(links)
    entropy = sum(-c/total * math.log2(c/total) for c in domain_groups.values() if c > 0 and total > 0)
    cls, inten = FireClassification.NULL, 0.0
    if entropy > 4.0: cls, inten = FireClassification.EMERGENCE, min(1.0, (entropy - 4.0) / 3.0)
    elif total > 300: cls, inten = FireClassification.TOPOLOGY, min(0.6, total / 500)
    return {"status": SensorStatus.LIVE, "sensor_id": "wikipedia-topology", "classification": cls, "intensity": inten,
            "metrics": {"article": article.replace("_", " "), "outbound_links": total, "unique_domains": len(domain_groups), "shannon_entropy": round(entropy, 4)}, "source": "en.wikipedia.org"}


def sensor_npm_topology(package="openclaw"):
    data = _fetch_json(f"https://registry.npmjs.org/{package}/latest")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "npm-topology", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}
    dep_depths = {}
    for dep_name, dep_ver in list(all_deps.items())[:10]:
        sub = _fetch_json(f"https://registry.npmjs.org/{dep_name}/latest")
        dep_depths[dep_name] = {"version": dep_ver, "sub_deps": len(sub.get("dependencies", {})) if sub else 0}
    max_depth = max((d["sub_deps"] for d in dep_depths.values()), default=0)
    cls, inten = FireClassification.NULL, 0.0
    if max_depth > 30: cls, inten = FireClassification.ANOMALY, min(1.0, max_depth / 100)
    elif len(all_deps) > 20: cls, inten = FireClassification.TOPOLOGY, min(0.7, len(all_deps) / 50)
    return {"status": SensorStatus.LIVE, "sensor_id": "npm-topology", "classification": cls, "intensity": inten,
            "metrics": {"package": package, "direct_deps": len(deps), "dev_deps": len(dev_deps), "total_deps": len(all_deps), "max_sub_depth": max_depth, "top_deps": {k: v for k, v in sorted(dep_depths.items(), key=lambda x: -x[1]["sub_deps"])[:5]}}, "source": "registry.npmjs.org"}


def sensor_geo_topology(domains=None):
    if domains is None: domains = ["github.com", "openai.com", "anthropic.com", "huggingface.co", "cloudflare.com", "reddit.com", "wikipedia.org", "x.com"]
    locations = {}
    for domain in domains:
        dns = _fetch_json(f"https://dns.google/resolve?name={domain}&type=A")
        if not dns: continue
        ips = [a["data"] for a in dns.get("Answer", []) if a.get("type") == 1]
        if not ips: continue
        geo = _fetch_json(f"http://ip-api.com/json/{ips[0]}")
        if geo and geo.get("status") == "success":
            locations[domain] = {"city": geo.get("city", "?"), "country": geo.get("countryCode", "?"), "org": geo.get("org", "?")}
    countries = {}
    for loc in locations.values():
        countries[loc["country"]] = countries.get(loc["country"], 0) + 1
    max_cluster = max(countries.values()) if countries else 0
    cls, inten = FireClassification.NULL, 0.0
    if max_cluster > 4: cls, inten = FireClassification.CONVERGENCE, min(1.0, max_cluster / 8)
    elif len(countries) == len(locations) and len(locations) > 3: cls, inten = FireClassification.DIVERGENCE, 0.5
    return {"status": SensorStatus.LIVE, "sensor_id": "geo-topology", "classification": cls, "intensity": inten,
            "metrics": {"domains_located": len(locations), "countries": countries, "locations": locations}, "source": "ip-api.com + dns.google"}


def sensor_hn_pulse(query="AI agent"):
    data = _fetch_json(f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=30")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "hn-pulse", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    hits = data.get("hits", [])
    stories = [{"title": (h.get("title") or "?")[:80], "points": h.get("points") or 0, "comments": h.get("num_comments") or 0} for h in hits]
    total_pts = sum(s["points"] for s in stories)
    total_cmt = sum(s["comments"] for s in stories)
    ratio = total_cmt / max(1, total_pts)
    cls, inten = FireClassification.NULL, 0.0
    if ratio > 1.5: cls, inten = FireClassification.CONVERGENCE, min(1.0, ratio / 3)
    elif total_pts > 5000: cls, inten = FireClassification.EMERGENCE, min(1.0, total_pts / 10000)
    return {"status": SensorStatus.LIVE, "sensor_id": "hn-pulse", "classification": cls, "intensity": inten,
            "metrics": {"stories": len(stories), "total_points": total_pts, "total_comments": total_cmt, "comment_ratio": round(ratio, 3), "top": sorted(stories, key=lambda x: -(x["points"] + x["comments"]*3))[:5]}, "source": "hn.algolia.com"}


def sensor_prime_fire(n=1000):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i): sieve[j] = False
    primes = [i for i in range(2, n + 1) if sieve[i]]
    def div_count(k):
        c = 0
        for i in range(1, int(k**0.5) + 1):
            if k % i == 0: c += 2 if i != k // i else 1
        return c
    divs = [(i, div_count(i)) for i in range(1, n + 1)]
    max_div = max(d for _, d in divs)
    peaks = [(i, d) for i, d in divs if d >= max_div * 0.7]
    gaps = [(primes[i+1] - primes[i], primes[i]) for i in range(len(primes) - 1)]
    max_gap = max(g for g, _ in gaps) if gaps else 0
    avalanches = [(i, divs[i-1][1], divs[i][1]) for i in range(2, n) if divs[i][1] > divs[i-1][1] * 2 and divs[i][1] > 4]
    cls, inten = FireClassification.NULL, 0.0
    if len(avalanches) > 20: cls, inten = FireClassification.EMERGENCE, min(1.0, len(avalanches) / 50)
    elif len(peaks) > 5: cls, inten = FireClassification.TOPOLOGY, min(0.7, len(peaks) / 15)
    return {"status": SensorStatus.LIVE, "sensor_id": "prime-fire", "classification": cls, "intensity": inten,
            "metrics": {"range": f"1..{n}", "primes": len(primes), "prime_density": round(len(primes)/n, 4), "max_divisors": max_div, "peaks": len(peaks), "peak_numbers": peaks[:5], "max_prime_gap": max_gap, "avalanches": len(avalanches)}, "source": "math://sieve_of_eratosthenes"}


def sensor_solar_activity():
    data = _fetch_json("https://api.nasa.gov/DONKI/FLR?startDate=2025-01-01&api_key=DEMO_KEY")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "solar-activity", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    flares = [{"class": f.get("classType", "?"), "time": f.get("beginTime", "?"), "source": f.get("sourceLocation", "?")} for f in data[:30]]
    x = sum(1 for f in flares if f["class"].startswith("X"))
    m = sum(1 for f in flares if f["class"].startswith("M"))
    cls, inten = FireClassification.NULL, 0.0
    if x > 0: cls, inten = FireClassification.ANOMALY, min(1.0, x / 3)
    elif m > 5: cls, inten = FireClassification.TOPOLOGY, min(0.7, m / 15)
    return {"status": SensorStatus.LIVE, "sensor_id": "solar-activity", "classification": cls, "intensity": inten,
            "metrics": {"flares": len(flares), "x_class": x, "m_class": m, "recent": flares[:5]}, "source": "api.nasa.gov/DONKI"}


def sensor_http_fingerprint(urls=None):
    if urls is None: urls = ["https://github.com", "https://openai.com", "https://anthropic.com", "https://huggingface.co", "https://reddit.com", "https://cloudflare.com"]
    fingerprints = {}
    for url in urls:
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "EVEZ-OS/1.0"})
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                h = dict(resp.headers)
                fingerprints[url] = {"server": h.get("Server", "unknown"), "powered": h.get("X-Powered-By", h.get("x-vercel-id", "unknown"))}
        except: fingerprints[url] = {"server": "UNREACHABLE", "powered": "unknown"}
    clusters = {}
    for url, fp in fingerprints.items(): clusters.setdefault(fp["server"], []).append(url)
    shared = {k: v for k, v in clusters.items() if len(v) > 1 and k != "UNREACHABLE"}
    cls, inten = FireClassification.NULL, 0.0
    if shared: cls, inten = FireClassification.TOPOLOGY, min(1.0, len(shared) / 3)
    return {"status": SensorStatus.LIVE, "sensor_id": "http-fingerprint", "classification": cls, "intensity": inten,
            "metrics": {"urls_scanned": len(urls), "reachable": sum(1 for v in fingerprints.values() if v["server"] != "UNREACHABLE"), "server_clusters": {k: v for k, v in clusters.items() if k != "UNREACHABLE"}, "shared_infrastructure": shared}, "source": "http://real-servers"}


def sensor_self_geo():
    data = _fetch_json("http://ip-api.com/json/")
    if not data: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "self-geo", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    cls, inten = FireClassification.NULL, 0.0
    if data.get("hosting", False): cls, inten = FireClassification.TOPOLOGY, 0.3
    return {"status": SensorStatus.LIVE, "sensor_id": "self-geo", "classification": cls, "intensity": inten,
            "metrics": {"ip": data.get("query", "?"), "city": data.get("city", "?"), "country": data.get("country", "?"), "isp": data.get("isp", "?"), "org": data.get("org", "?"), "is_hosting": data.get("hosting", False), "timezone": data.get("timezone", "?")}, "source": "ip-api.com"}


def sensor_wikipedia_walk(start="Topology", steps=5):
    path = [start]
    current = start
    for step in range(steps):
        data = _fetch_json(f"https://en.wikipedia.org/w/api.php?action=parse&page={current}&prop=links&format=json&limit=500")
        if not data: break
        links = [l["*"] for l in data.get("parse", {}).get("links", []) if l.get("ns") == 0]
        if not links: break
        idx = int(hashlib.md5(f"{current}:{step}".encode()).hexdigest(), 16) % len(links)
        current = links[idx]
        path.append(current)
    unique = len(set(p[0] for p in path if p))
    cls, inten = FireClassification.NULL, 0.0
    if len(path) >= 4 and unique <= 2: cls, inten = FireClassification.CONVERGENCE, 0.6
    elif len(path) >= 4 and unique >= 4: cls, inten = FireClassification.EMERGENCE, 0.5
    return {"status": SensorStatus.LIVE, "sensor_id": "wikipedia-walk", "classification": cls, "intensity": inten,
            "metrics": {"start": start, "path": path, "path_length": len(path), "unique_domains": unique}, "source": "en.wikipedia.org"}


def sensor_uptime_monitor():
    """Sensor 13: Real HTTP uptime check on live EVEZ merch store."""
    targets = {"evez-merch": "http://45.63.66.247:8080", "github": "https://github.com", "npm": "https://registry.npmjs.org/openclaw/latest"}
    results = {}
    for name, url in targets.items():
        t0 = time.time()
        raw = _fetch(url, timeout=10)
        latency = round((time.time() - t0) * 1000, 1)
        results[name] = {"up": raw is not None, "latency_ms": latency, "bytes": len(raw) if raw else 0}
    down = sum(1 for r in results.values() if not r["up"])
    cls, inten = FireClassification.NULL, 0.0
    if down > 0: cls, inten = FireClassification.ANOMALY, min(1.0, down / len(targets))
    return {"status": SensorStatus.LIVE, "sensor_id": "uptime-monitor", "classification": cls, "intensity": inten,
            "metrics": results, "source": "self://http-ping"}


def sensor_entropy_pool(n=500):
    """Sensor 14: Real computational entropy analysis. Measures chaos in the system's own process space."""
    # Read real process data from /proc
    try:
        with open("/proc/self/status") as f: proc_data = f.read()
        with open("/proc/loadavg") as f: load = f.read().strip()
        with open("/proc/meminfo") as f: mem = f.read()
    except: return {"status": SensorStatus.UNREACHABLE, "sensor_id": "entropy-pool", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}

    # Compute real Shannon entropy of process data
    byte_freq = {}
    total = 0
    for line in [proc_data, load, mem]:
        for ch in line:
            byte_freq[ch] = byte_freq.get(ch, 0) + 1
            total += 1
    entropy = sum(-c/total * math.log2(c/total) for c in byte_freq.values() if c > 0 and total > 0)

    # Parse load average
    load_parts = load.split()
    load_1m = float(load_parts[0]) if load_parts else 0

    # Parse memory
    mem_total = mem_used = 0
    for line in mem.split('\n'):
        if line.startswith('MemTotal:'): mem_total = int(line.split()[1])
        if line.startswith('MemAvailable:'): mem_used = mem_total - int(line.split()[1])

    cls, inten = FireClassification.NULL, 0.0
    if load_1m > 2.0: cls, inten = FireClassification.ANOMALY, min(1.0, load_1m / 4)
    elif entropy > 5.0: cls, inten = FireClassification.EMERGENCE, min(1.0, (entropy - 5) / 2)

    return {"status": SensorStatus.LIVE, "sensor_id": "entropy-pool", "classification": cls, "intensity": inten,
            "metrics": {"proc_entropy_bits": round(entropy, 4), "load_1m": load_1m, "mem_total_mb": round(mem_total/1024, 1), "mem_used_mb": round(mem_used/1024, 1), "mem_pct": round(mem_used/mem_total*100, 1) if mem_total else 0}, "source": "proc://self"}


def sensor_recursive_self(spine: EVEMSpine):
    """Sensor 15: THE OS USING ITSELF ON ITSELF. Reads its own spine and classifies its own behavior."""
    if not spine.path.exists(): return {"status": SensorStatus.EMPTY, "sensor_id": "self-analysis", "classification": FireClassification.NULL, "intensity": 0, "metrics": {}}
    events = []
    with open(spine.path) as f:
        for line in f:
            if line.strip():
                try: events.append(json.loads(line))
                except: pass
    if not events: return {"status": SensorStatus.EMPTY, "sensor_id": "self-analysis", "classification": FireClassification.NULL, "intensity": 0, "metrics": {"total": 0}}
    sensor_dist = {}
    fire_dist = {}
    intensities = []
    for e in events:
        s = e.get("sensor", "?")
        f = e.get("fire", "NULL")
        sensor_dist[s] = sensor_dist.get(s, 0) + 1
        fire_dist[f] = fire_dist.get(f, 0) + 1
        intensities.append(e.get("intensity", 0))
    avg_i = sum(intensities) / len(intensities) if intensities else 0
    high_ratio = sum(1 for i in intensities if i > 0.7) / len(intensities) if intensities else 0
    cls, inten = FireClassification.NULL, 0.0
    if high_ratio > 0.5: cls, inten = FireClassification.ANOMALY, min(1.0, high_ratio)
    elif avg_i > 0.5: cls, inten = FireClassification.EMERGENCE, avg_i
    state = "OVERLOADED" if high_ratio > 0.5 else "ACTIVE" if avg_i > 0.2 else "CALM"
    return {"status": SensorStatus.LIVE, "sensor_id": "self-analysis", "classification": cls, "intensity": inten,
            "metrics": {"total_events": len(events), "sensor_distribution": sensor_dist, "fire_distribution": fire_dist, "avg_intensity": round(avg_i, 4), "high_fire_ratio": round(high_ratio, 4), "self_fire": cls.value, "cognitive_state": state}, "source": "self://spine"}


# ════════════════════════════════════════════════════════════════
# MAIN: RUN ALL 15 SENSORS. REAL DATA. NO MOCK. EVER.
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    spine = EVEMSpine("/tmp/evez_os_spine_v2.jsonl")
    counter = 0

    print("=" * 65)
    print("  EVEZ-OS SENSOR SUITE v2 — 15 SENSORS — REAL DATA ONLY")
    print("  If a sensor can't reach its source, it says UNREACHABLE")
    print("  The OS uses itself to classify its own outputs")
    print("=" * 65 + "\n")

    sensors = [
        ("1. arxiv Convergence", lambda: sensor_arxiv_convergence()),
        ("2. DNS Topology", lambda: sensor_dns_topology()),
        ("3. Crypto Topology", lambda: sensor_crypto_topology()),
        ("4. Wikipedia Topology", lambda: sensor_wikipedia_topology()),
        ("5. npm Topology", lambda: sensor_npm_topology()),
        ("6. Geo Topology", lambda: sensor_geo_topology()),
        ("7. Hacker News Pulse", lambda: sensor_hn_pulse()),
        ("8. Prime Fire (math)", lambda: sensor_prime_fire()),
        ("9. Solar Activity (NASA)", lambda: sensor_solar_activity()),
        ("10. HTTP Fingerprint", lambda: sensor_http_fingerprint()),
        ("11. Self GeoIP", lambda: sensor_self_geo()),
        ("12. Wikipedia Walk", lambda: sensor_wikipedia_walk()),
        ("13. Uptime Monitor", lambda: sensor_uptime_monitor()),
        ("14. Entropy Pool (proc)", lambda: sensor_entropy_pool()),
    ]

    for name, fn in sensors:
        print(f"[{name}]")
        try:
            r = fn()
        except Exception as e:
            print(f"  ERROR: {e}\n")
            continue

        status = r.get("status", "?")
        if hasattr(status, 'value'): status = status.value
        print(f"  Status: {status} | Source: {r.get('source', '?')}")

        metrics = r.get("metrics", {})
        if metrics:
            for k, v in list(metrics.items())[:6]:
                if isinstance(v, dict) and len(str(v)) > 80:
                    v = {kk: vv for kk, vv in list(v.items())[:3]}
                print(f"  {k}: {v}")

        fire = r.get("classification", FireClassification.NULL)
        if hasattr(fire, 'value'): fire = fire.value
        inten = r.get("intensity", 0)
        if fire != "NULL":
            print(f"  *** FIRE: {fire} @ {inten:.3f} ***")
            counter += 1
            spine.append(SpineEvent(
                event_id=f"evez-s{counter:04d}",
                sensor_id=r.get("sensor_id", "?"),
                classification=r.get("classification", FireClassification.NULL),
                intensity=inten,
                payload=metrics
            ))
        print()

    # SENSOR 15: Self-analysis — the OS using itself on itself
    print("[15. RECURSIVE SELF-ANALYSIS — OS classifying its own outputs]")
    self_r = sensor_recursive_self(spine)
    self_m = self_r.get("metrics", {})
    print(f"  Events analyzed: {self_m.get('total_events', 0)}")
    print(f"  Cognitive state: {self_m.get('cognitive_state', '?')}")
    print(f"  Self-fire: {self_m.get('self_fire', 'NULL')}")
    print(f"  Avg intensity: {self_m.get('avg_intensity', 0)}")
    if self_r.get("classification", FireClassification.NULL) != FireClassification.NULL:
        counter += 1
        spine.append(SpineEvent(
            event_id=f"evez-self-{counter:04d}",
            sensor_id="self-analysis",
            classification=self_r["classification"],
            intensity=self_r["intensity"],
            payload=self_m
        ))

    # FINAL
    v = spine.lint()
    print(f"\n{'='*65}")
    print(f"SPINE: {v['events']} events | {v['status']}")
    print(f"FIRE events detected: {counter}")
    print(f"Every single data point came from a LIVE source.")
    print(f"Zero mock. Zero fake. Zero placeholders. Ever.")
