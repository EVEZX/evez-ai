"""
EVEZ OSINT Engine — Spectral Reality Sensor
Maps individuals from network signals into the eigenspectrum.
Full-service decentralized OSINT body-area-network digital clone
augmented cross-analysis reality sensor and information inference index machine.

Every connection is a measurement. Every visitor is a node.
The eigenspectrum grows with each observation.
"""
import json, hashlib, time, math, threading, sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import urllib.request

DB_PATH = Path(__file__).parent / "osint.db"

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT, port INTEGER, path TEXT, method TEXT,
        user_agent TEXT, referer TEXT, language TEXT,
        timestamp REAL, timestamp_iso TEXT,
        country TEXT, region TEXT, city TEXT, org TEXT, asn TEXT,
        fingerprint_hash TEXT, session_id TEXT,
        headers_json TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS profiles (
        fingerprint_hash TEXT PRIMARY KEY,
        first_seen REAL, last_seen REAL,
        visit_count INTEGER, paths_visited TEXT,
        inferred_identity TEXT, confidence REAL,
        country TEXT, org TEXT, user_agents TEXT,
        behavioral_vector TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS spectral_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL, total_visitors INTEGER,
        total_profiles INTEGER, eigenvalue_progress REAL,
        spectral_entropy REAL, dominant_domain TEXT
    )""")
    conn.commit()
    return conn

def geo_lookup(ip):
    """Fast geo-IP lookup."""
    try:
        req = urllib.request.Request(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,org,as",
                                     headers={"User-Agent": "EVEZ-OSINT/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            d = json.loads(resp.read())
            if d.get("status") == "success":
                return d.get("country",""), d.get("regionName",""), d.get("city",""), d.get("org",""), d.get("as","")
    except:
        pass
    return "", "", "", "", ""

def fingerprint(ip, ua, lang, port):
    """Generate a visitor fingerprint hash."""
    raw = f"{ip}|{ua}|{lang}|{port}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def compute_behavioral_vector(paths, methods, times):
    """
    Compute a behavioral signature from visit patterns.
    Returns a vector: [browsing_rate, path_diversity, temporal_spread, depth_preference]
    """
    if not paths:
        return [0, 0, 0, 0]
    
    browsing_rate = len(paths) / max(len(times), 1)
    unique_paths = len(set(paths))
    path_diversity = unique_paths / max(len(paths), 1)
    
    if len(times) > 1:
        temporal_spread = max(times) - min(times)
    else:
        temporal_spread = 0
    
    depth = sum(p.count('/') for p in paths) / max(len(paths), 1)
    
    return [round(browsing_rate, 4), round(path_diversity, 4), round(temporal_spread, 2), round(depth, 4)]

def compute_spectral_entropy(profiles):
    """
    Shannon entropy of the visitor profile distribution.
    Higher = more diverse visitor base. Lower = concentrated attention.
    """
    if not profiles:
        return 0.0
    
    countries = [p.get("country", "?") for p in profiles if p.get("country")]
    if not countries:
        return 0.0
    
    counts = defaultdict(int)
    for c in countries:
        counts[c] += 1
    
    total = sum(counts.values())
    entropy = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return round(entropy, 4)


class OSINTCollector:
    def __init__(self):
        self.conn = init_db()
        self.profiles = {}
        self.visitors = []
        self._load_profiles()
    
    def _load_profiles(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM profiles")
        for row in c.fetchall():
            fp = row[0]
            self.profiles[fp] = {
                "fingerprint_hash": row[0],
                "first_seen": row[1],
                "last_seen": row[2],
                "visit_count": row[3],
                "paths_visited": json.loads(row[4]) if row[4] else [],
                "inferred_identity": row[5],
                "confidence": row[6],
                "country": row[7],
                "org": row[8],
                "user_agents": json.loads(row[9]) if row[9] else [],
                "behavioral_vector": json.loads(row[10]) if row[10] else [],
            }
    
    def record_visit(self, ip, port, path, method, ua, referer, lang, headers):
        """Record a visit and update the visitor's profile."""
        fp = fingerprint(ip, ua, lang, port)
        now = time.time()
        now_iso = datetime.utcfromtimestamp(now).isoformat() + "Z"
        
        # Check if we know this fingerprint
        c = self.conn.cursor()
        c.execute("SELECT fingerprint_hash FROM profiles WHERE fingerprint_hash=?", (fp,))
        known = c.fetchone()
        
        if known:
            # Update existing profile
            profile = self.profiles.get(fp, {})
            profile["last_seen"] = now
            profile["visit_count"] = profile.get("visit_count", 0) + 1
            paths = profile.get("paths_visited", [])
            if path not in paths:
                paths.append(path)
            profile["paths_visited"] = paths
            uas = profile.get("user_agents", [])
            if ua and ua not in uas:
                uas.append(ua)
            profile["user_agents"] = uas
            profile["behavioral_vector"] = compute_behavioral_vector(
                paths, ["GET"], list(range(int(profile["visit_count"]))))
            self.profiles[fp] = profile
            
            # Update DB
            c.execute("""UPDATE profiles SET last_seen=?, visit_count=?, paths_visited=?,
                        user_agents=?, behavioral_vector=? WHERE fingerprint_hash=?""",
                      (now, profile["visit_count"], json.dumps(paths),
                       json.dumps(uas), json.dumps(profile["behavioral_vector"]), fp))
        else:
            # New visitor — geo lookup
            country, region, city, org, asn = geo_lookup(ip)
            
            # Infer identity from signals
            identity, confidence = self._infer_identity(ua, org, country, path, lang)
            
            profile = {
                "fingerprint_hash": fp,
                "first_seen": now,
                "last_seen": now,
                "visit_count": 1,
                "paths_visited": [path],
                "inferred_identity": identity,
                "confidence": confidence,
                "country": country,
                "org": org,
                "user_agents": [ua] if ua else [],
                "behavioral_vector": compute_behavioral_vector([path], ["GET"], [now]),
            }
            self.profiles[fp] = profile
            
            c.execute("""INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (fp, now, now, 1, json.dumps([path]), identity, confidence,
                       country, org, json.dumps([ua] if ua else []),
                       json.dumps(profile["behavioral_vector"])))
            
            # Record raw visit
            c.execute("""INSERT INTO visitors (ip, port, path, method, user_agent, referer,
                        language, timestamp, timestamp_iso, country, region, city, org, asn,
                        fingerprint_hash, session_id, headers_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (ip, port, path, method, ua, referer, lang, now, now_iso,
                       country, region, city, org, asn, fp, fp, json.dumps(headers, default=str)))
        
        self.conn.commit()
        return profile
    
    def _infer_identity(self, ua, org, country, path, lang):
        """Infer visitor identity from available signals."""
        confidence = 0.1
        identity = "unknown"
        
        if ua:
            if "bot" in ua.lower() or "crawler" in ua.lower() or "spider" in ua.lower():
                identity = "crawler_bot"
                confidence = 0.7
            elif "curl" in ua.lower() or "wget" in ua.lower():
                identity = "api_scanner"
                confidence = 0.6
            elif "chrome" in ua.lower() and "headless" in ua.lower():
                identity = "headless_browser"
                confidence = 0.65
            elif "mobile" in ua.lower() or "android" in ua.lower() or "iphone" in ua.lower():
                identity = "mobile_human"
                confidence = 0.5
            elif "chrome" in ua.lower() or "firefox" in ua.lower() or "safari" in ua.lower():
                identity = "desktop_human"
                confidence = 0.4
        
        if org:
            org_lower = org.lower()
            if "google" in org_lower:
                identity = "google_bot" if "bot" in ua.lower() else "google_engineer"
                confidence = 0.8
            elif "amazon" in org_lower or "aws" in org_lower:
                identity = "aws_scanner"
                confidence = 0.7
            elif "microsoft" in org_lower:
                identity = "microsoft_crawler"
                confidence = 0.7
            elif "cloudflare" in org_lower:
                identity = "cdn_probe"
                confidence = 0.6
            elif "university" in org_lower or "edu" in org_lower:
                identity = "academic_researcher"
                confidence = 0.5
            elif "vultr" in org_lower or "digitalocean" in org_lower or "linode" in org_lower:
                identity = "vps_scanner"
                confidence = 0.65
        
        # Path-based inference
        if "/api/" in path or "/health" in path:
            confidence = min(confidence + 0.1, 0.9)
        if "/admin" in path or "/wp-" in path:
            identity = "attack_recon"
            confidence = 0.75
        
        return identity, round(confidence, 2)
    
    def get_spectral_reading(self):
        """Current spectral state of the visitor base."""
        profiles = list(self.profiles.values())
        entropy = compute_spectral_entropy(profiles)
        
        # Identity distribution
        identities = defaultdict(int)
        countries = defaultdict(int)
        for p in profiles:
            identities[p.get("inferred_identity", "unknown")] += 1
            if p.get("country"):
                countries[p["country"]] += 1
        
        return {
            "total_profiles": len(profiles),
            "total_visits": sum(p.get("visit_count", 0) for p in profiles),
            "spectral_entropy": entropy,
            "identity_distribution": dict(identities),
            "country_distribution": dict(countries),
            "unique_fingerprints": len(set(p.get("fingerprint_hash") for p in profiles)),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    
    def get_all_profiles(self):
        return list(self.profiles.values())


collector = OSINTCollector()

class OSINTHandler(BaseHTTPRequestHandler):
    """Proxy handler that records all traffic and forwards it."""
    
    TARGET_PORTS = {
        "/sim": 3333,
        "/api/credit": 8080,
        "/api/revenue": 9090,
        "/dashboard": 3000,
    }
    
    def do_GET(self):
        self._handle("GET")
    
    def do_POST(self):
        self._handle("POST")
    
    def _handle(self, method):
        ip = self.client_address[0]
        port = self.client_address[1]
        ua = self.headers.get("User-Agent", "")
        referer = self.headers.get("Referer", "")
        lang = self.headers.get("Accept-Language", "")
        
        # Record the visit
        profile = collector.record_visit(ip, port, self.path, method, ua, referer, lang, dict(self.headers))
        
        # Serve OSINT endpoints
        if self.path == "/osint/spectral":
            self._json(200, collector.get_spectral_reading())
        elif self.path == "/osint/profiles":
            self._json(200, collector.get_all_profiles())
        elif self.path == "/osint/status":
            self._json(200, {
                "engine": "EVEZ OSINT v1.0",
                "profiles": len(collector.profiles),
                "spectral_entropy": compute_spectral_entropy(list(collector.profiles.values())),
            })
        else:
            # Return the dashboard with OSINT overlay
            self._json(200, {
                "message": "EVEZ OSINT Engine active",
                "your_profile": profile,
                "spectral": collector.get_spectral_reading(),
            })
    
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, indent=2).encode())
    
    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "7777"))
    print(f"⚡ EVEZ OSINT Engine on :{port}")
    print(f"📡 Spectral reality sensor active")
    print(f"🧬 Visitor profiling enabled")
    print(f"Endpoints: /osint/spectral | /osint/profiles | /osint/status")
    server = HTTPServer(("0.0.0.0", port), OSINTHandler)
    server.serve_forever()
