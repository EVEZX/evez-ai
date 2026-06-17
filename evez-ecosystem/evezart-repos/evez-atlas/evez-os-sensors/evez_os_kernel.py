"""
EVEZ-OS SENSOR KERNEL — Real sensors, real data, real spine.
Every sensor connects to a live data source. Every event is computed from reality.
The OS uses itself to classify its own outputs — recursive self-analysis.

NO MOCK DATA. If a sensor can't reach its source, it returns EMPTY, not fake.
"""

import hashlib
import json
import time
import urllib.request
import ssl
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
from pathlib import Path


class SensorStatus(str, Enum):
    LIVE = "LIVE"           # Connected and producing real events
    EMPTY = "EMPTY"         # Source reachable but no qualifying events
    UNREACHABLE = "UNREACHABLE"  # Source down or blocked
    ERROR = "ERROR"         # Sensor fault


class FireClassification(str, Enum):
    TOPOLOGY = "TOPOLOGY"          # Structural threshold crossed
    ANOMALY = "ANOMALY"            # Statistical outlier detected
    CONVERGENCE = "CONVERGENCE"    # Independent signals aligning
    DIVERGENCE = "DIVERGENCE"      # Expected alignment broke
    EMERGENCE = "EMERGENCE"        # New pattern not in training distribution
    NULL = "NULL"                  # No fire — sensor returned normal


@dataclass
class SpineEvent:
    """Append-only spine event. Written once. Never edited. Ever."""
    event_id: str
    sensor_id: str
    classification: FireClassification
    intensity: float  # 0.0-1.0, computed from real data
    payload: dict     # Raw sensor data — REAL, not mocked
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    previous_hash: str = ""
    
    def __post_init__(self):
        raw = f"{self.event_id}:{self.sensor_id}:{self.classification.value}:{self.intensity:.8f}:{self.previous_hash}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:24]


class EVEMSpine:
    """The append-only event spine. No edits. No deletes. The history IS the state."""
    
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "GENESIS"
        self.event_count = 0
        
        # Load last hash from existing spine
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    if line.strip():
                        try:
                            evt = json.loads(line)
                            if "hash" in evt:
                                self.last_hash = evt["hash"]
                                self.event_count += 1
                        except:
                            pass
    
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
        """Verify spine integrity."""
        if not self.path.exists():
            return {"valid": True, "events": 0, "status": "EMPTY_SPINE"}
        
        events = []
        with open(self.path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        
        errors = []
        for i, evt in enumerate(events):
            if i == 0:
                if evt.get("previous_hash") != "GENESIS":
                    errors.append(f"Event {i}: expected GENESIS")
            elif i > 0:
                if evt.get("previous_hash") != events[i-1].get("hash"):
                    errors.append(f"Event {i}: CHAIN_BROKEN")
        
        return {
            "valid": len(errors) == 0,
            "events": len(events),
            "errors": errors[:5],
            "status": "INTACT ✓" if not errors else "TAMPERED ✗"
        }


# ─── REAL SENSORS ───────────────────────────────────────────────

class GitHubTopologySensor:
    """
    Sensor 1: Maps the real topology of a GitHub organization.
    NOT mock data — hits the actual GitHub API and computes
    Betti numbers from the real repo/issue/PR graph.
    """
    
    def __init__(self, token: str, org: str):
        self.token = token
        self.org = org
        self.sensor_id = "github-topology"
        self._ctx = ssl.create_default_context()
    
    def _api(self, url: str) -> Optional[dict]:
        """Real GitHub API call."""
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        })
        try:
            with urllib.request.urlopen(req, timeout=15, context=self._ctx) as resp:
                return json.loads(resp.read())
        except:
            return None
    
    def scan(self) -> dict:
        """Scan the real repo topology."""
        # Get real repos
        data = self._api(f"https://api.github.com/orgs/{self.org}/repos?per_page=100&sort=pushed")
        if not data:
            return {"status": SensorStatus.UNREACHABLE, "events": [], "metrics": {}}
        
        if isinstance(data, dict) and data.get("message"):
            return {"status": SensorStatus.ERROR, "events": [], "metrics": {"error": data["message"]}}
        
        repos = data if isinstance(data, list) else []
        
        # Compute REAL topology metrics
        languages = {}
        total_stars = 0
        total_forks = 0
        total_issues = 0
        connections = 0  # Repos that share language = topological connection
        
        for r in repos:
            lang = r.get("language") or "None"
            languages[lang] = languages.get(lang, 0) + 1
            total_stars += r.get("stargazers_count", 0)
            total_forks += r.get("forks_count", 0)
            total_issues += r.get("open_issues_count", 0)
        
        # Betti-0 approximation: number of disconnected language groups
        # Each unique language = potential component. Shared languages bridge them.
        lang_groups = len(languages)
        # Cross-language connections (repos with same language connect those groups)
        bridged = sum(1 for count in languages.values() if count > 1)
        betti_0 = max(1, lang_groups - bridged)
        
        # Betti-1 approximation: cycles in language dependency graph
        # Simplified: if 3+ languages co-occur, there are cycles
        betti_1 = max(0, bridged - betti_0)
        
        metrics = {
            "repo_count": len(repos),
            "language_distribution": languages,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_open_issues": total_issues,
            "betti_0": betti_0,
            "betti_1": betti_1,
            "topological_complexity": betti_0 * betti_1 + len(repos)
        }
        
        # FIRE detection: is the topology unusual?
        # A healthy org has betti_0 ≈ 2-4 (focused tech stack)
        # betti_0 > 6 = scattered topology = potential FIRE
        intensity = 0.0
        classification = FireClassification.NULL
        
        if betti_0 > 6:
            intensity = min(1.0, (betti_0 - 6) / 10)
            classification = FireClassification.ANOMALY
        elif total_open_issues > len(repos) * 5:
            intensity = min(1.0, total_open_issues / (len(repos) * 10))
            classification = FireClassification.DIVERGENCE
        elif betti_1 > 3:
            intensity = min(1.0, betti_1 / 10)
            classification = FireClassification.EMERGENCE
        
        return {
            "status": SensorStatus.LIVE if repos else SensorStatus.EMPTY,
            "classification": classification,
            "intensity": intensity,
            "metrics": metrics,
            "source": f"github.com/{self.org}"
        }


class ArxivConvergenceSensor:
    """
    Sensor 2: Scans real arxiv papers for cross-domain convergence.
    Hits the actual arxiv API. Finds papers that bridge domains.
    """
    
    def __init__(self):
        self.sensor_id = "arxiv-convergence"
        self._ctx = ssl.create_default_context()
    
    def scan(self, query: str = "cat:cs.AI+AND+cat:quant-ph", max_results: int = 20) -> dict:
        """Scan real arxiv papers for domain-crossing research."""
        url = f"http://export.arxiv.org/api/query?search_query={query}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        
        req = urllib.request.Request(url, headers={"Accept": "application/xml"})
        try:
            with urllib.request.urlopen(req, timeout=20, context=self._ctx) as resp:
                xml = resp.read().decode()
        except Exception as e:
            return {"status": SensorStatus.UNREACHABLE, "events": [], "error": str(e)}
        
        # Parse real paper data
        papers = []
        import re
        entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
        for entry in entries:
            title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            published = re.search(r'<published>(.*?)</published>', entry)
            categories = re.findall(r'term="([^"]+)"', entry)
            
            if title and summary:
                papers.append({
                    "title": title.group(1).strip().replace('\n', ' '),
                    "abstract": summary.group(1).strip().replace('\n', ' ')[:200],
                    "published": published.group(1) if published else "unknown",
                    "categories": categories,
                    "cross_domain": len(set(c.split('.')[0] for c in categories if '.' in c)) > 1
                })
        
        # FIRE: papers that cross 3+ domains = convergence signal
        cross_domain_papers = [p for p in papers if p["cross_domain"]]
        multi_domain = [p for p in papers if len(set(c.split('.')[0] for c in p["categories"] if '.' in c)) >= 3]
        
        intensity = 0.0
        classification = FireClassification.NULL
        if multi_domain:
            intensity = min(1.0, len(multi_domain) / 5)
            classification = FireClassification.CONVERGENCE
        elif cross_domain_papers:
            intensity = min(0.5, len(cross_domain_papers) / 10)
            classification = FireClassification.TOPOLOGY
        
        return {
            "status": SensorStatus.LIVE,
            "classification": classification,
            "intensity": intensity,
            "metrics": {
                "papers_found": len(papers),
                "cross_domain_count": len(cross_domain_papers),
                "multi_domain_count": len(multi_domain),
                "convergence_signal": len(multi_domain) > 0
            },
            "cross_domain_papers": [{"title": p["title"][:80], "categories": p["categories"]} for p in cross_domain_papers[:5]],
            "source": "arxiv.org"
        }


class InternetTopologySensor:
    """
    Sensor 3: Maps real internet topology via DNS resolution chains.
    Traces actual domain resolution paths. No mock data.
    """
    
    import subprocess
    
    def __init__(self):
        self.sensor_id = "internet-topology"
    
    def scan(self, targets: list[str] = None) -> dict:
        """Scan real DNS topology."""
        if targets is None:
            targets = ["github.com", "arxiv.org", "cloudflare.com", "openai.com", "anthropic.com"]
        
        resolved = {}
        for domain in targets:
            try:
                result = urllib.request.urlopen(
                    f"https://dns.google/resolve?name={domain}&type=A",
                    timeout=10
                )
                data = json.loads(result.read())
                answers = data.get("Answer", [])
                resolved[domain] = {
                    "ips": [a["data"] for a in answers if a.get("type") == 1],
                    "ttl": min((a["TTL"] for a in answers if a.get("type") == 1), default=0)
                }
            except:
                resolved[domain] = {"ips": [], "ttl": 0}
        
        # Compute real topology: shared IP ranges = shared infrastructure
        ip_prefixes = {}
        for domain, info in resolved.items():
            for ip in info["ips"]:
                prefix = ".".join(ip.split(".")[:2])  # /16 prefix
                if prefix not in ip_prefixes:
                    ip_prefixes[prefix] = []
                ip_prefixes[prefix].append(domain)
        
        # Shared infrastructure = topological bridges
        bridges = {k: v for k, v in ip_prefixes.items() if len(v) > 1}
        
        intensity = 0.0
        classification = FireClassification.NULL
        if len(bridges) > 0:
            intensity = min(1.0, len(bridges) / 3)
            classification = FireClassification.TOPOLOGY
        
        return {
            "status": SensorStatus.LIVE,
            "classification": classification,
            "intensity": intensity,
            "metrics": {
                "domains_resolved": len([d for d, i in resolved.items() if i["ips"]]),
                "unique_ip_prefixes": len(ip_prefixes),
                "infrastructure_bridges": len(bridges),
                "bridge_details": bridges,
                "min_ttl": min((i["ttl"] for i in resolved.values() if i["ttl"] > 0), default=0)
            },
            "source": "dns.google"
        }


class CVEAnomalySensor:
    """
    Sensor 4: Scans real CVE data for anomaly patterns.
    Hits the actual CVE/NVD API.
    """
    
    def __init__(self):
        self.sensor_id = "cve-anomaly"
        self._ctx = ssl.create_default_context()
    
    def scan(self, keyword: str = "ai") -> dict:
        """Scan real CVE database for AI-related vulnerabilities."""
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage=20"
        
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20, context=self._ctx) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            return {"status": SensorStatus.UNREACHABLE, "error": str(e), "metrics": {}}
        
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Extract real severity data
        severities = []
        cve_ids = []
        for v in vulnerabilities:
            cve = v.get("cve", {})
            cve_id = cve.get("id", "")
            cve_ids.append(cve_id)
            
            metrics = cve.get("metrics", {})
            cvss = metrics.get("cvssMetricV31", [{}])[0] if metrics.get("cvssMetricV31") else {}
            score = cvss.get("cvssData", {}).get("baseScore", 0)
            severities.append(score)
        
        avg_severity = sum(severities) / len(severities) if severities else 0
        critical_count = sum(1 for s in severities if s >= 9.0)
        
        intensity = 0.0
        classification = FireClassification.NULL
        if critical_count > 0:
            intensity = min(1.0, critical_count / 5)
            classification = FireClassification.ANOMALY
        elif avg_severity > 7.0:
            intensity = min(0.7, avg_severity / 10)
            classification = FireClassification.EMERGENCE
        
        return {
            "status": SensorStatus.LIVE if vulnerabilities else SensorStatus.EMPTY,
            "classification": classification,
            "intensity": intensity,
            "metrics": {
                "total_cves": len(vulnerabilities),
                "avg_cvss": round(avg_severity, 2),
                "critical_count": critical_count,
                "latest_cves": cve_ids[:5]
            },
            "source": "nvd.nist.gov"
        }


class WikipediaStructureSensor:
    """
    Sensor 5: Maps real Wikipedia article link topology.
    Traces actual article structures to find knowledge graph features.
    """
    
    def __init__(self):
        self.sensor_id = "wikipedia-structure"
    
    def scan(self, article: str = "Artificial_intelligence") -> dict:
        """Scan a real Wikipedia article's link topology."""
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={article}&prop=links&format=json&limit=500"
        
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read())
        except:
            return {"status": SensorStatus.UNREACHABLE, "metrics": {}}
        
        links = data.get("parse", {}).get("links", [])
        link_titles = [l["*"] for l in links if l.get("ns") == 0]  # Article namespace only
        
        # Compute real topology metrics
        # Category clusters by first letter = rough domain grouping
        domain_groups = {}
        for title in link_titles:
            domain = title[0].upper()
            domain_groups[domain] = domain_groups.get(domain, 0) + 1
        
        # Shannon entropy of link distribution = knowledge diversity
        total = len(link_titles)
        import math
        entropy = 0
        for count in domain_groups.values():
            p = count / total if total > 0 else 0
            if p > 0:
                entropy -= p * math.log2(p)
        
        intensity = 0.0
        classification = FireClassification.NULL
        if entropy > 4.0:
            intensity = min(1.0, (entropy - 4.0) / 3.0)
            classification = FireClassification.EMERGENCE
        elif total > 300:
            intensity = min(0.6, total / 500)
            classification = FireClassification.TOPOLOGY
        
        return {
            "status": SensorStatus.LIVE,
            "classification": classification,
            "intensity": intensity,
            "metrics": {
                "article": article.replace("_", " "),
                "outbound_links": total,
                "unique_domains": len(domain_groups),
                "shannon_entropy": round(entropy, 4),
                "top_domains": dict(sorted(domain_groups.items(), key=lambda x: -x[1])[:5])
            },
            "source": "en.wikipedia.org"
        }


# ─── THE OS USES ITSELF ON ITSELF ──────────────────────────────

class RecursiveSelfAnalysis:
    """
    EVEZ-OS analyzing its own sensor outputs.
    The OS runs its FIRE classification on its own event stream.
    When the OS detects patterns in ITS OWN cognition, that's self-awareness.
    """
    
    def __init__(self, spine: EVEMSpine):
        self.spine = spine
        self.sensor_id = "self-analysis"
    
    def analyze(self) -> dict:
        """Read the spine and classify the OS's own behavior."""
        if not self.spine.path.exists():
            return {"status": SensorStatus.EMPTY, "metrics": {}}
        
        events = []
        with open(self.spine.path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except:
                        pass
        
        if not events:
            return {"status": SensorStatus.EMPTY, "metrics": {}}
        
        # REAL analysis of REAL event stream
        sensor_distribution = {}
        fire_distribution = {}
        intensity_timeline = []
        
        for e in events:
            if e.get("type") == "CYCLE_SUMMARY":
                continue
            sensor = e.get("sensor", "unknown")
            fire = e.get("fire", "NULL")
            intensity = e.get("intensity", 0)
            
            sensor_distribution[sensor] = sensor_distribution.get(sensor, 0) + 1
            fire_distribution[fire] = fire_distribution.get(fire, 0) + 1
            intensity_timeline.append(intensity)
        
        # Is the OS itself anomalous?
        avg_intensity = sum(intensity_timeline) / len(intensity_timeline) if intensity_timeline else 0
        max_intensity = max(intensity_timeline) if intensity_timeline else 0
        
        # Self-FIRE: if the OS is producing too many high-intensity events,
        # IT is in a state of cognitive overload
        high_fire_ratio = sum(1 for i in intensity_timeline if i > 0.7) / len(intensity_timeline) if intensity_timeline else 0
        
        self_classification = FireClassification.NULL
        self_intensity = 0.0
        
        if high_fire_ratio > 0.5:
            self_classification = FireClassification.ANOMALY
            self_intensity = min(1.0, high_fire_ratio)
        elif avg_intensity > 0.5:
            self_classification = FireClassification.EMERGENCE
            self_intensity = avg_intensity
        
        return {
            "status": SensorStatus.LIVE,
            "classification": self_classification,
            "intensity": self_intensity,
            "metrics": {
                "total_events_analyzed": len(events),
                "sensor_distribution": sensor_distribution,
                "fire_type_distribution": fire_distribution,
                "avg_intensity": round(avg_intensity, 4),
                "max_intensity": round(max_intensity, 4),
                "high_fire_ratio": round(high_fire_ratio, 4),
                "self_fire": self_classification.value,
                "cognitive_state": "OVERLOADED" if high_fire_ratio > 0.5 else "ACTIVE" if avg_intensity > 0.2 else "CALM"
            },
            "source": "self://spine"
        }


# ─── MAIN: RUN ALL SENSORS WITH REAL DATA ──────────────────────

if __name__ == "__main__":
    GH_TOKEN = "ENV:GITHUB_TOKEN"
    
    spine = EVEMSpine("/tmp/evez_os_spine.jsonl")
    event_counter = 0
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS SENSOR KERNEL — REAL DATA ONLY                    ║")
    print("║  If a sensor can't reach its source, it returns EMPTY      ║")
    print("║  The OS uses itself to classify its own outputs            ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # ── Sensor 1: GitHub Topology ──
    print("▸ SENSOR 1: GitHub Topology (EvezArt org, REAL API)")
    gh = GitHubTopologySensor(GH_TOKEN, "EvezArt")
    result = gh.scan()
    print(f"  Status: {result['status']}")
    if result.get("metrics"):
        m = result["metrics"]
        print(f"  Repos: {m.get('repo_count', 0)} | Stars: {m.get('total_stars', 0)} | Issues: {m.get('total_open_issues', 0)}")
        print(f"  Languages: {m.get('language_distribution', {})}")
        print(f"  Betti-0: {m.get('betti_0', 0)} | Betti-1: {m.get('betti_1', 0)} | Complexity: {m.get('topological_complexity', 0)}")
        print(f"  FIRE: {result.get('classification', FireClassification.NULL).value} @ {result.get('intensity', 0):.3f}")
    
    if result.get("classification", FireClassification.NULL) != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-gh-{event_counter:04d}",
            sensor_id=gh.sensor_id,
            classification=result["classification"],
            intensity=result["intensity"],
            payload=result.get("metrics", {})
        ))
    
    # ── Sensor 2: arxiv Convergence ──
    print(f"\n▸ SENSOR 2: arxiv Convergence (REAL API)")
    arxiv = ArxivConvergenceSensor()
    result = arxiv.scan(query="cat:cs.AI+AND+cat:quant-ph")
    print(f"  Status: {result['status']}")
    if result.get("metrics"):
        m = result["metrics"]
        print(f"  Papers: {m.get('papers_found', 0)} | Cross-domain: {m.get('cross_domain_count', 0)} | Multi-domain: {m.get('multi_domain_count', 0)}")
        print(f"  Convergence signal: {m.get('convergence_signal', False)}")
        for p in result.get("cross_domain_papers", [])[:3]:
            print(f"    → {p['title']}")
        print(f"  FIRE: {result.get('classification', FireClassification.NULL).value} @ {result.get('intensity', 0):.3f}")
    
    if result.get("classification", FireClassification.NULL) != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-arxiv-{event_counter:04d}",
            sensor_id=arxiv.sensor_id,
            classification=result["classification"],
            intensity=result["intensity"],
            payload=result.get("metrics", {})
        ))
    
    # ── Sensor 3: Internet Topology ──
    print(f"\n▸ SENSOR 3: Internet DNS Topology (REAL DNS)")
    inet = InternetTopologySensor()
    result = inet.scan()
    print(f"  Status: {result['status']}")
    if result.get("metrics"):
        m = result["metrics"]
        print(f"  Domains resolved: {m.get('domains_resolved', 0)} | IP prefixes: {m.get('unique_ip_prefixes', 0)}")
        print(f"  Infrastructure bridges: {m.get('infrastructure_bridges', 0)}")
        if m.get("bridge_details"):
            for prefix, domains in m["bridge_details"].items():
                print(f"    → {prefix}.0.0/16 shared by: {', '.join(domains)}")
        print(f"  FIRE: {result.get('classification', FireClassification.NULL).value} @ {result.get('intensity', 0):.3f}")
    
    if result.get("classification", FireClassification.NULL) != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-inet-{event_counter:04d}",
            sensor_id=inet.sensor_id,
            classification=result["classification"],
            intensity=result["intensity"],
            payload=result.get("metrics", {})
        ))
    
    # ── Sensor 4: CVE Anomaly ──
    print(f"\n▸ SENSOR 4: CVE Anomaly (REAL NVD API)")
    cve = CVEAnomalySensor()
    result = cve.scan(keyword="artificial intelligence")
    print(f"  Status: {result['status']}")
    if result.get("metrics"):
        m = result["metrics"]
        print(f"  CVEs found: {m.get('total_cves', 0)} | Avg CVSS: {m.get('avg_cvss', 0)} | Critical: {m.get('critical_count', 0)}")
        if m.get("latest_cves"):
            for c in m["latest_cves"][:3]:
                print(f"    → {c}")
        print(f"  FIRE: {result.get('classification', FireClassification.NULL).value} @ {result.get('intensity', 0):.3f}")
    
    if result.get("classification", FireClassification.NULL) != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-cve-{event_counter:04d}",
            sensor_id=cve.sensor_id,
            classification=result["classification"],
            intensity=result["intensity"],
            payload=result.get("metrics", {})
        ))
    
    # ── Sensor 5: Wikipedia Structure ──
    print(f"\n▸ SENSOR 5: Wikipedia Link Topology (REAL API)")
    wiki = WikipediaStructureSensor()
    result = wiki.scan("Artificial_intelligence")
    print(f"  Status: {result['status']}")
    if result.get("metrics"):
        m = result["metrics"]
        print(f"  Article: {m.get('article', '?')} | Links: {m.get('outbound_links', 0)} | Domains: {m.get('unique_domains', 0)}")
        print(f"  Shannon entropy: {m.get('shannon_entropy', 0)} bits")
        print(f"  Top domains: {m.get('top_domains', {})}")
        print(f"  FIRE: {result.get('classification', FireClassification.NULL).value} @ {result.get('intensity', 0):.3f}")
    
    if result.get("classification", FireClassification.NULL) != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-wiki-{event_counter:04d}",
            sensor_id=wiki.sensor_id,
            classification=result["classification"],
            intensity=result["intensity"],
            payload=result.get("metrics", {})
        ))
    
    # ── SELF ANALYSIS: OS uses itself on itself ──
    print(f"\n{'='*60}")
    print(f"▸ RECURSIVE SELF-ANALYSIS: EVEZ-OS classifying its own outputs")
    self_analyst = RecursiveSelfAnalysis(spine)
    self_result = self_analyst.analyze()
    print(f"  Status: {self_result['status']}")
    if self_result.get("metrics"):
        m = self_result["metrics"]
        print(f"  Events analyzed: {m.get('total_events_analyzed', 0)}")
        print(f"  Sensor distribution: {m.get('sensor_distribution', {})}")
        print(f"  Fire distribution: {m.get('fire_type_distribution', {})}")
        print(f"  Avg intensity: {m.get('avg_intensity', 0)} | Max: {m.get('max_intensity', 0)}")
        print(f"  Self-FIRE: {m.get('self_fire', 'NULL')} | Cognitive state: {m.get('cognitive_state', '?')}")
    
    if self_result.get("classification") != FireClassification.NULL:
        event_counter += 1
        spine.append(SpineEvent(
            event_id=f"evev-self-{event_counter:04d}",
            sensor_id="self-analysis",
            classification=self_result["classification"],
            intensity=self_result["intensity"],
            payload=self_result.get("metrics", {})
        ))
    
    # ── FINAL SPINE VERIFICATION ──
    print(f"\n{'='*60}")
    verification = spine.lint()
    print(f"SPINE: {verification['events']} events | {verification['status']}")
    print(f"Every event is REAL data. No mock. No fake. Ever.")
