"""EVEZ-OS Live Demo Data Aggregator — single API call that returns everything."""
import httpx
import json
import time
import numpy as np

async def fetch_all() -> dict:
    """Fetch live data from all EVEZ-OS services simultaneously."""
    results = {}
    async with httpx.AsyncClient(timeout=10) as client:
        # Disclosure spectral analysis
        try:
            resp = await client.get("http://127.0.0.1:8087/api/v1/demo")
            results["disclosure"] = resp.json()
        except Exception as e:
            results["disclosure"] = {"error": str(e)}

        # IGRE genome + speedrun
        try:
            resp = await client.get("http://127.0.0.1:8099/api/v1/integration/disclosure")
            results["igre"] = resp.json()
        except Exception as e:
            results["igre"] = {"error": str(e)}

        # Spectral correlation
        try:
            resp = await client.get("http://127.0.0.1:8103/api/v1/correlate")
            results["spectral"] = resp.json()
        except Exception as e:
            results["spectral"] = {"error": str(e)}

        # Funding pipeline
        try:
            resp = await client.get("http://127.0.0.1:8101/api/v1/pipeline")
            results["funding"] = resp.json()
        except Exception as e:
            results["funding"] = {"error": str(e)}

        # Service status
        try:
            resp = await client.get("http://127.0.0.1:8102/api/v1/status")
            results["status"] = resp.json()
        except Exception as e:
            results["status"] = {"error": str(e)}

    return results
