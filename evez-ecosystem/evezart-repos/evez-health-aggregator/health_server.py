from fastapi import FastAPI
import concurrent.futures
import urllib.request
import time

app = FastAPI(title="EVEZ Health Aggregator", version="1.0.0")

PORTS = {
    8080: 'ClawBreak', 8081: 'Cognition', 8082: 'MAES', 8083: 'Bridge',
    8875: 'Omega', 8876: 'Ledger', 8891: 'Factory', 8892: 'Research',
    8893: 'Mesh', 8894: 'MeshBroker', 8896: 'Psyche', 8898: 'DigitalTwin',
    8900: 'Livestream', 8904: 'Commerce', 8905: 'Search', 8906: 'Cloud',
    8907: 'Guard', 8908: 'ThreatHunter', 8909: 'Federation', 8910: 'Profit',
    8911: 'Observatory', 8913: 'SongDecon', 8914: 'MemeEngine', 8950: 'Manifold'
}

def check_port(port):
    start = time.time()
    try:
        urllib.request.urlopen(f'http://localhost:{port}/health', timeout=3)
        return {'service': PORTS[port], 'port': port, 'status': 'UP', 'ms': int((time.time() - start) * 1000)}
    except:
        return {'service': PORTS[port], 'port': port, 'status': 'DOWN', 'ms': 0}

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '1.0.0', 'service': 'evez-health-aggregator', 'ts': int(time.time())}

@app.get('/scan')
def scan():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(check_port, PORTS.keys()))
    up = sum(1 for r in results if r['status'] == 'UP')
    return {'total': len(results), 'up': up, 'down': len(results) - up, 'services': results}

@app.get('/summary')
def summary():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(check_port, PORTS.keys()))
    up = sum(1 for r in results if r['status'] == 'UP')
    return {'total': len(results), 'up': up, 'down': len(results) - up}