#!/usr/bin/env python3
"""
EVEZ SENTINEL — Port 10009
Website security scanner. Headers, TLS, vulnerabilities, grade A-F.
$0/month. No API keys needed.
"""
import json, time, sqlite3, hashlib
from aiohttp import web
import aiohttp

PORT = 10009
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/sentinel/sentinel.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS scans (
        id TEXT PRIMARY KEY, url TEXT, grade TEXT, score INTEGER,
        headers TEXT, findings TEXT, timestamp REAL
    );
""")
DB.commit()

SECURITY_HEADERS = {
    "strict-transport-security": {"weight": 15, "message": "HSTS — forces HTTPS"},
    "content-security-policy": {"weight": 20, "message": "CSP — prevents XSS/injection"},
    "x-content-type-options": {"weight": 5, "message": "Prevents MIME sniffing"},
    "x-frame-options": {"weight": 10, "message": "Prevents clickjacking"},
    "x-xss-protection": {"weight": 5, "message": "Browser XSS filter"},
    "referrer-policy": {"weight": 5, "message": "Controls referrer leakage"},
    "permissions-policy": {"weight": 5, "message": "Controls feature access"},
    "cross-origin-opener-policy": {"weight": 10, "message": "Prevents cross-origin attacks"},
    "cross-origin-resource-policy": {"weight": 5, "message": "Controls resource sharing"},
    "x-permitted-cross-domain-policies": {"weight": 5, "message": "Controls Flash/PDF access"},
}

async def scan_url(url):
    """Scan a URL for security headers and issues"""
    findings = []
    score = 100
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15),
                                   ssl=False, allow_redirects=True) as resp:
                headers = dict(resp.headers)
                status = resp.status
                final_url = str(resp.url)
    except Exception as e:
        return {"error": str(e)[:100], "grade": "F", "score": 0}

    # Check security headers
    header_results = {}
    for header, config in SECURITY_HEADERS.items():
        present = header in headers or header.replace("-", "-").lower() in {k.lower(): v for k, v in headers.items()}
        header_results[header] = {"present": present, "message": config["message"]}
        if not present:
            score -= config["weight"]
            findings.append({"severity": "medium" if config["weight"] >= 10 else "low",
                            "header": header, "issue": f"Missing {header}", "fix": config["message"]})

    # Check HTTPS
    if not url.startswith("https://"):
        score -= 10
        findings.append({"severity": "high", "issue": "No HTTPS", "fix": "Enable TLS/SSL"})

    # Check server info leakage
    server = headers.get("Server", "")
    if server and any(pkg in server.lower() for pkg in ["apache", "nginx", "php", "express"]):
        findings.append({"severity": "low", "issue": f"Server version exposed: {server}", "fix": "Remove Server header"})

    # Grade
    score = max(0, score)
    grade = "A+" if score >= 95 else "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D" if score >= 30 else "F"
    
    return {"grade": grade, "score": score, "headers": header_results,
            "findings": findings, "status_code": status, "final_url": final_url}

async def handle_scan(req):
    url = req.query.get("url", "")
    if not url:
        return web.json_response({"error": "url parameter required"}, status=400)
    if not url.startswith("http"):
        url = f"https://{url}"
    
    result = await scan_url(url)
    scan_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:10]
    
    DB.execute("INSERT INTO scans VALUES (?,?,?,?,?,?,?)",
              (scan_id, url, result.get("grade", "?"), result.get("score", 0),
               json.dumps(result.get("headers", {})), json.dumps(result.get("findings", [])), time.time()))
    DB.commit()
    
    return web.json_response({"id": scan_id, "url": url, **result})

async def handle_history(req):
    rows = DB.execute("SELECT * FROM scans ORDER BY timestamp DESC LIMIT 50").fetchall()
    return web.json_response({"scans": [dict(r) for r in rows]})

async def handle_health(req):
    scans = DB.execute("SELECT COUNT(*) as c FROM scans").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-sentinel",
                             "total_scans": scans, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_get("/v1/scan", handle_scan)
app.router.add_get("/v1/history", handle_history)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/sentinel", exist_ok=True)
    print(f"🛡️ EVEZ Sentinel → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
