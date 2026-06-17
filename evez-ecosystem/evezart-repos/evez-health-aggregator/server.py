from fastapi import FastAPI
import concurrent.futures
import urllib.request
import time

app = FastAPI(title="EVEZ Health Aggregator", version="1.0.0")

PORTS = {
    8080: 'ClawBreak', 8081: 'VCL', 8082: 'Commerce', 8083: 'Guard',
    8084: 'Mesh', 8085: 'HealthAgg', 8086: 'RevenueBridge',
    8090: 'Spine', 8091: 'CriticalMind',
    18789: 'OpenClaw Gateway'
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
