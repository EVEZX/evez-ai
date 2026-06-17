#!/usr/bin/env python3
"""EVEZ Pulse — Health check monitor for EVEZ services"""
import asyncio, logging, json, os
import httpx
import yaml
from pydantic import BaseModel
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('evez-pulse')

class Service(BaseModel):
    name: str
    url: str
    expected_status: int = 200

class PulseConfig(BaseModel):
    services: List[Service]
    slack_webhook: Optional[str] = None
    check_interval: int = 60

async def check_service(service: Service) -> dict:
    """Ping a service and return its status"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(service.url)
            up = r.status_code == service.expected_status
            return {"name": service.name, "status": "UP" if up else "DEGRADED", "code": r.status_code}
    except Exception as e:
        return {"name": service.name, "status": "DOWN", "error": str(e)}

def load_config(path: str = 'config.yaml') -> PulseConfig:
    with open(path) as f:
        return PulseConfig(**yaml.safe_load(f))

async def run_pulse(config: PulseConfig) -> dict:
    """Check all services and return results"""
    results = await asyncio.gather(*[check_service(s) for s in config.services])
    summary = {
        "total": len(results),
        "up": sum(1 for r in results if r["status"] == "UP"),
        "down": sum(1 for r in results if r["status"] == "DOWN"),
        "services": results
    }
    return summary

def main():
    config = load_config()
    result = asyncio.run(run_pulse(config))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
