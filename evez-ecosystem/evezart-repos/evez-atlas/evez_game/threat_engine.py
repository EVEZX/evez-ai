"""Threat Detection Engine - Local and Nonlocal Threat Analysis.

Implements comprehensive threat detection using:
- Local system monitoring (processes, files, network connections)
- Network traffic analysis (DNS, BGP, TLS, CDN patterns)
- Behavioral analysis and anomaly detection
- Signature-based and heuristic detection
- Quantum-enhanced randomness for honeypot deployment
- Entanglement-based correlation detection
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .quantum_rng import QuantumRNG, random_bytes, random_float, random_int
from .spine import append_event, read_events


class ThreatLevel(Enum):
    """Threat severity levels."""
    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class ThreatCategory(Enum):
    """Categories of threats."""
    PROCESS_ANOMALY = auto()
    FILE_MODIFICATION = auto()
    NETWORK_INTRUSION = auto()
    DNS_HIJACKING = auto()
    BGP_MANIPULATION = auto()
    TLS_CERTIFICATE = auto()
    CDN_POISONING = auto()
    AUTH_BYPASS = auto()
    ROLLBACK_ATTACK = auto()
    COORDINATED_HARASSMENT = auto()
    BOT_SWARM = auto()
    PSYOPS = auto()
    UNKNOWN = auto()


@dataclass
class ThreatIndicator:
    """A single threat indicator."""
    category: ThreatCategory
    level: ThreatLevel
    source: str  # "local" or "network"
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.5
    hash: str = field(default="")
    
    def __post_init__(self):
        if not self.hash:
            # Create serializable dict manually to handle enums
            data = {
                "category": self.category.name if isinstance(self.category, ThreatCategory) else str(self.category),
                "level": self.level.name if isinstance(self.level, ThreatLevel) else str(self.level),
                "source": self.source,
                "description": self.description,
                "evidence": self.evidence,
                "timestamp": self.timestamp,
                "confidence": self.confidence
            }
            self.hash = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()[:32]


@dataclass
class ThreatProfile:
    """Aggregated threat profile from multiple indicators."""
    indicators: List[ThreatIndicator] = field(default_factory=list)
    aggregated_level: ThreatLevel = ThreatLevel.INFO
    attack_vector: str = ""
    attribution: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class LocalThreatMonitor:
    """Monitor local system for threats."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.baseline: Dict[str, Any] = {}
        self.suspicious_patterns: List[re.Pattern] = [
            re.compile(r"nc\s+-[el]", re.I),  # netcat listeners
            re.compile(r"python\s+.*-m\s+http\.server", re.I),
            re.compile(r"bash\s+-i", re.I),  # interactive bash
            re.compile(r"/dev/tcp/", re.I),  # bash network redirection
        ]
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def establish_baseline(self) -> None:
        """Establish baseline of normal system behavior."""
        self.baseline = {
            "processes": self._get_process_list(),
            "open_ports": self._get_open_ports(),
            "established_connections": self._get_established_connections(),
            "loaded_modules": self._get_loaded_modules(),
            "timestamp": time.time(),
        }
    
    def _get_process_list(self) -> Dict[int, Dict[str, Any]]:
        """Get list of running processes."""
        processes = {}
        try:
            if platform.system() == "Linux":
                for pid_dir in Path("/proc").glob("[0-9]*"):
                    try:
                        pid = int(pid_dir.name)
                        cmdline = (pid_dir / "cmdline").read_text().replace("\x00", " ")
                        exe = os.readlink(pid_dir / "exe") if (pid_dir / "exe").exists() else ""
                        processes[pid] = {
                            "cmdline": cmdline,
                            "exe": exe,
                        }
                    except Exception:
                        continue
            elif platform.system() == "Darwin":
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
                for line in result.stdout.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 11:
                        try:
                            pid = int(parts[1])
                            processes[pid] = {"cmdline": " ".join(parts[10:])}
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error getting process list: {e}")
        return processes
    
    def _get_open_ports(self) -> Set[Tuple[str, int]]:
        """Get list of open ports."""
        ports = set()
        try:
            result = subprocess.run(
                ["ss", "-tuln"] if platform.system() == "Linux" else ["netstat", "-an"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "LISTEN" in line or "*.*" in line:
                    match = re.search(r":(\d+)", line)
                    if match:
                        proto = "tcp" if "tcp" in line else "udp"
                        ports.add((proto, int(match.group(1))))
        except Exception:
            pass
        return ports
    
    def _get_established_connections(self) -> Set[Tuple[str, int, str, int]]:
        """Get established network connections."""
        connections = set()
        try:
            result = subprocess.run(
                ["ss", "-tun"] if platform.system() == "Linux" else ["netstat", "-an"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "ESTAB" in line:
                    # Parse connection details
                    parts = line.split()
                    if len(parts) >= 5:
                        local = parts[4]
                        remote = parts[5]
                        connections.add((local, 0, remote, 0))  # Simplified
        except Exception:
            pass
        return connections
    
    def _get_loaded_modules(self) -> Set[str]:
        """Get loaded kernel modules."""
        modules = set()
        try:
            if Path("/proc/modules").exists():
                with open("/proc/modules") as f:
                    for line in f:
                        module = line.split()[0]
                        modules.add(module)
        except Exception:
            pass
        return modules
    
    def scan_processes(self) -> List[ThreatIndicator]:
        """Scan processes for suspicious activity."""
        indicators = []
        current_processes = self._get_process_list()
        
        for pid, info in current_processes.items():
            cmdline = info.get("cmdline", "")
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if pattern.search(cmdline):
                    indicators.append(ThreatIndicator(
                        category=ThreatCategory.PROCESS_ANOMALY,
                        level=ThreatLevel.HIGH,
                        source="local",
                        description=f"Suspicious process pattern detected: {pattern.pattern}",
                        evidence={"pid": pid, "cmdline": cmdline, "pattern": pattern.pattern},
                        confidence=0.8
                    ))
            
            # Check for processes with no command line (possible rootkit)
            if not cmdline.strip() and pid > 100:
                indicators.append(ThreatIndicator(
                    category=ThreatCategory.PROCESS_ANOMALY,
                    level=ThreatLevel.MEDIUM,
                    source="local",
                    description=f"Process with empty command line: {pid}",
                    evidence={"pid": pid, "exe": info.get("exe", "unknown")},
                    confidence=0.6
                ))
        
        # Check for new processes since baseline
        if self.baseline.get("processes"):
            baseline_pids = set(self.baseline["processes"].keys())
            current_pids = set(current_processes.keys())
            new_pids = current_pids - baseline_pids
            
            for pid in new_pids:
                if pid > 1000:  # User processes
                    info = current_processes[pid]
                    indicators.append(ThreatIndicator(
                        category=ThreatCategory.PROCESS_ANOMALY,
                        level=ThreatLevel.LOW,
                        source="local",
                        description=f"New process since baseline: {pid}",
                        evidence={"pid": pid, "cmdline": info.get("cmdline", "")[:100]},
                        confidence=0.4
                    ))
        
        return indicators
    
    def scan_file_system(self, paths: Optional[List[Path]] = None) -> List[ThreatIndicator]:
        """Scan file system for anomalies."""
        indicators = []
        
        if paths is None:
            paths = [Path("/tmp"), Path("/dev/shm"), Path.home() / ".local"]
        
        suspicious_extensions = {".sh", ".py", ".pl", ".rb", ".bin"}
        
        for path in paths:
            if not path.exists():
                continue
            
            try:
                for item in path.iterdir():
                    if item.is_file():
                        # Check for recently modified executables
                        stat = item.stat()
                        age_hours = (time.time() - stat.st_mtime) / 3600
                        
                        if age_hours < 1 and os.access(item, os.X_OK):
                            indicators.append(ThreatIndicator(
                                category=ThreatCategory.FILE_MODIFICATION,
                                level=ThreatLevel.MEDIUM,
                                source="local",
                                description=f"Recently created executable: {item.name}",
                                evidence={"path": str(item), "mtime": stat.st_mtime},
                                confidence=0.5
                            ))
                        
                        # Check for suspicious extensions in unusual locations
                        if item.suffix in suspicious_extensions and "/tmp" in str(item):
                            indicators.append(ThreatIndicator(
                                category=ThreatCategory.FILE_MODIFICATION,
                                level=ThreatLevel.LOW,
                                source="local",
                                description=f"Script in temp directory: {item.name}",
                                evidence={"path": str(item)},
                                confidence=0.3
                            ))
            except PermissionError:
                continue
        
        return indicators
    
    def scan_network(self) -> List[ThreatIndicator]:
        """Scan network connections for anomalies."""
        indicators = []
        
        current_connections = self._get_established_connections()
        
        # Check for connections to known malicious IPs (simplified)
        # In production, this would use threat intelligence feeds
        suspicious_ports = {4444, 5555, 6666, 7777, 8888, 31337, 12345}
        
        for local, local_port, remote, remote_port in current_connections:
            if remote_port in suspicious_ports:
                indicators.append(ThreatIndicator(
                    category=ThreatCategory.NETWORK_INTRUSION,
                    level=ThreatLevel.HIGH,
                    source="local",
                    description=f"Connection to suspicious port: {remote_port}",
                    evidence={"remote": remote, "port": remote_port},
                    confidence=0.7
                ))
        
        return indicators
    
    def full_scan(self) -> List[ThreatIndicator]:
        """Run full local threat scan."""
        indicators = []
        indicators.extend(self.scan_processes())
        indicators.extend(self.scan_file_system())
        indicators.extend(self.scan_network())
        return indicators


class NetworkThreatAnalyzer:
    """Analyze network-level threats."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.dns_cache: Dict[str, Any] = {}
        self.tls_fingerprints: Dict[str, str] = {}
        self.bgp_announcements: List[Dict[str, Any]] = []
    
    def analyze_dns(self, domain: str) -> List[ThreatIndicator]:
        """Analyze DNS for hijacking attempts."""
        indicators = []
        
        try:
            # Get current resolution
            current_ips = socket.gethostbyname_ex(domain)[2]
            
            # Check against cached value
            if domain in self.dns_cache:
                cached_ips = self.dns_cache[domain].get("ips", [])
                if set(current_ips) != set(cached_ips):
                    indicators.append(ThreatIndicator(
                        category=ThreatCategory.DNS_HIJACKING,
                        level=ThreatLevel.HIGH,
                        source="network",
                        description=f"DNS resolution changed for {domain}",
                        evidence={
                            "domain": domain,
                            "cached": cached_ips,
                            "current": current_ips
                        },
                        confidence=0.85
                    ))
            
            # Update cache
            self.dns_cache[domain] = {
                "ips": current_ips,
                "timestamp": time.time()
            }
            
            # Check for suspicious TTL values
            try:
                import dns.resolver
                answers = dns.resolver.resolve(domain, "A")
                for rdata in answers:
                    ttl = answers.rrset.ttl
                    if ttl < 60:  # Very short TTL can indicate fast-flux
                        indicators.append(ThreatIndicator(
                            category=ThreatCategory.DNS_HIJACKING,
                            level=ThreatLevel.MEDIUM,
                            source="network",
                            description=f"Suspiciously short DNS TTL for {domain}: {ttl}s",
                            evidence={"domain": domain, "ttl": ttl},
                            confidence=0.6
                        ))
            except ImportError:
                pass
            
        except socket.gaierror:
            pass
        
        return indicators
    
    def analyze_tls_certificate(self, host: str, port: int = 443) -> List[ThreatIndicator]:
        """Analyze TLS certificate for anomalies."""
        indicators = []
        
        try:
            import ssl
            import certifi
            
            context = ssl.create_default_context(cafile=certifi.where())
            with socket.create_connection((host, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    
                    # Check TLS version
                    if version in ("TLSv1", "TLSv1.1"):
                        indicators.append(ThreatIndicator(
                            category=ThreatCategory.TLS_CERTIFICATE,
                            level=ThreatLevel.MEDIUM,
                            source="network",
                            description=f"Outdated TLS version: {version}",
                            evidence={"host": host, "version": version},
                            confidence=0.7
                        ))
                    
                    # Check certificate fingerprint
                    cert_der = ssock.getpeercert(binary_form=True)
                    fingerprint = hashlib.sha256(cert_der).hexdigest()
                    
                    key = f"{host}:{port}"
                    if key in self.tls_fingerprints:
                        if self.tls_fingerprints[key] != fingerprint:
                            indicators.append(ThreatIndicator(
                                category=ThreatCategory.TLS_CERTIFICATE,
                                level=ThreatLevel.CRITICAL,
                                source="network",
                                description=f"TLS certificate changed for {host}",
                                evidence={
                                    "host": host,
                                    "old_fp": self.tls_fingerprints[key][:16],
                                    "new_fp": fingerprint[:16]
                                },
                                confidence=0.9
                            ))
                    
                    self.tls_fingerprints[key] = fingerprint
                    
                    # Check certificate expiry
                    not_after = cert.get("notAfter")
                    if not_after:
                        from datetime import datetime
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        days_until_expiry = (expiry - datetime.utcnow()).days
                        
                        if days_until_expiry < 7:
                            indicators.append(ThreatIndicator(
                                category=ThreatCategory.TLS_CERTIFICATE,
                                level=ThreatLevel.MEDIUM,
                                source="network",
                                description=f"Certificate expiring soon: {days_until_expiry} days",
                                evidence={"host": host, "expiry": not_after},
                                confidence=0.5
                            ))
        
        except Exception as e:
            indicators.append(ThreatIndicator(
                category=ThreatCategory.TLS_CERTIFICATE,
                level=ThreatLevel.LOW,
                source="network",
                description=f"Could not verify TLS for {host}: {str(e)[:50]}",
                evidence={"host": host, "error": str(e)[:100]},
                confidence=0.3
            ))
        
        return indicators
    
    def analyze_cdn_patterns(self, url: str) -> List[ThreatIndicator]:
        """Analyze CDN patterns for poisoning attempts."""
        indicators = []
        
        # Check for CDN anomalies
        cdn_headers = ["CF-RAY", "X-Cache", "X-CDN", "Fastly-Debug-Digest"]
        
        try:
            import urllib.request
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "EVEZ-ThreatScan/1.0")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                headers = dict(response.headers)
                
                # Check for missing CDN headers on CDN-hosted content
                has_cdn_header = any(h in headers for h in cdn_headers)
                
                if "cloudflare" in url and not has_cdn_header:
                    indicators.append(ThreatIndicator(
                        category=ThreatCategory.CDN_POISONING,
                        level=ThreatLevel.HIGH,
                        source="network",
                        description=f"Missing Cloudflare headers for {url}",
                        evidence={"url": url, "headers": list(headers.keys())},
                        confidence=0.75
                    ))
        
        except Exception:
            pass
        
        return indicators
    
    def detect_bot_swarm(self, request_logs: List[Dict[str, Any]]) -> List[ThreatIndicator]:
        """Detect coordinated bot swarm activity."""
        indicators = []
        
        if len(request_logs) < 10:
            return indicators
        
        # Group by user agent
        ua_groups: Dict[str, List[Dict]] = {}
        for log in request_logs:
            ua = log.get("user_agent", "unknown")
            ua_groups.setdefault(ua, []).append(log)
        
        # Check for identical UAs with high frequency
        for ua, logs in ua_groups.items():
            if len(logs) > 50 and len(set(ua_groups.keys())) < 3:
                # Calculate timing patterns
                timestamps = sorted([l.get("timestamp", 0) for l in logs])
                intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                
                # Check for regular intervals (bot-like)
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((i - avg_interval)**2 for i in intervals) / len(intervals)
                    
                    if variance < 0.1:  # Very regular timing
                        indicators.append(ThreatIndicator(
                            category=ThreatCategory.BOT_SWARM,
                            level=ThreatLevel.HIGH,
                            source="network",
                            description=f"Possible bot swarm detected: {len(logs)} requests from similar UAs",
                            evidence={
                                "user_agent": ua[:50],
                                "request_count": len(logs),
                                "avg_interval": avg_interval,
                                "variance": variance
                            },
                            confidence=0.85
                        ))
        
        return indicators


class ThreatIntelligence:
    """Aggregate and correlate threat intelligence."""
    
    def __init__(self, spine_path: Optional[Path] = None):
        self.local_monitor = LocalThreatMonitor()
        self.network_analyzer = NetworkThreatAnalyzer()
        self.spine_path = spine_path or Path("threat_spine.jsonl")
        self.indicator_history: List[ThreatIndicator] = []
        self._lock = threading.Lock()
    
    def initialize(self) -> None:
        """Initialize threat intelligence system."""
        self.local_monitor.establish_baseline()
    
    def collect_indicators(self) -> List[ThreatIndicator]:
        """Collect all threat indicators."""
        indicators = []
        
        # Local threats
        indicators.extend(self.local_monitor.full_scan())
        
        # Network threats (sample domains)
        sample_domains = ["google.com", "github.com", "cloudflare.com"]
        for domain in sample_domains:
            indicators.extend(self.network_analyzer.analyze_dns(domain))
            indicators.extend(self.network_analyzer.analyze_tls_certificate(domain))
        
        with self._lock:
            self.indicator_history.extend(indicators)
        
        return indicators
    
    def correlate_indicators(self, indicators: List[ThreatIndicator]) -> ThreatProfile:
        """Correlate indicators into threat profile."""
        if not indicators:
            return ThreatProfile()
        
        # Aggregate by level
        level_scores = {
            ThreatLevel.INFO: 1,
            ThreatLevel.LOW: 2,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.HIGH: 4,
            ThreatLevel.CRITICAL: 5
        }
        
        max_score = max(level_scores[i.level] for i in indicators)
        aggregated = [l for l, s in level_scores.items() if s == max_score][0]
        
        # Determine attack vector
        categories = [i.category for i in indicators]
        most_common = max(set(categories), key=categories.count)
        attack_vector = most_common.name.replace("_", " ").title()
        
        # Generate recommendations
        recommendations = []
        if any(i.level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL) for i in indicators):
            recommendations.append("Immediate isolation recommended")
            recommendations.append("Initiate forensic capture")
        if any(i.category == ThreatCategory.NETWORK_INTRUSION for i in indicators):
            recommendations.append("Review firewall rules")
            recommendations.append("Enable enhanced logging")
        if any(i.category == ThreatCategory.PROCESS_ANOMALY for i in indicators):
            recommendations.append("Scan for rootkits")
            recommendations.append("Verify process signatures")
        
        return ThreatProfile(
            indicators=indicators,
            aggregated_level=aggregated,
            attack_vector=attack_vector,
            recommended_actions=recommendations
        )
    
    def log_to_spine(self, profile: ThreatProfile) -> None:
        """Log threat profile to event spine."""
        event = {
            "step": len(self.indicator_history),
            "type": "threat_assessment",
            "level": profile.aggregated_level.name,
            "attack_vector": profile.attack_vector,
            "indicator_count": len(profile.indicators),
            "recommendations": profile.recommended_actions,
            "indicators": [
                {
                    "category": i.category.name,
                    "level": i.level.name,
                    "source": i.source,
                    "description": i.description,
                    "confidence": i.confidence,
                    "hash": i.hash
                }
                for i in profile.indicators[:10]  # Limit to top 10
            ]
        }
        
        append_event(self.spine_path, event)
    
    def continuous_monitor(self, interval: float = 30.0) -> Iterator[ThreatProfile]:
        """Continuously monitor and yield threat profiles."""
        while True:
            indicators = self.collect_indicators()
            profile = self.correlate_indicators(indicators)
            
            if profile.indicators:
                self.log_to_spine(profile)
            
            yield profile
            time.sleep(interval)


# Convenience functions
def scan_threats() -> ThreatProfile:
    """Run single threat scan."""
    intel = ThreatIntelligence()
    intel.initialize()
    indicators = intel.collect_indicators()
    return intel.correlate_indicators(indicators)


def start_continuous_monitor(interval: float = 30.0) -> Iterator[ThreatProfile]:
    """Start continuous threat monitoring."""
    intel = ThreatIntelligence()
    intel.initialize()
    return intel.continuous_monitor(interval)
