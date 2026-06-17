
# ─── Live Demo Endpoint ──────────────────────────────────────

@app.get("/api/v1/live-demo")
async def live_demo():
    """Aggregate live data from all services — single call for the demo page."""
    import httpx
    
    results = {}
    async with httpx.AsyncClient(timeout=10) as client:
        # Disclosure spectral analysis
        try:
            resp = await client.get("http://127.0.0.1:8087/api/v1/demo")
            results["disclosure"] = resp.json()
        except: results["disclosure"] = {"offline": True}

        # IGRE genome + speedrun
        try:
            resp = await client.get("http://127.0.0.1:8099/api/v1/integration/disclosure")
            results["igre"] = resp.json()
        except: results["igre"] = {"offline": True}

        # Spectral correlation
        try:
            resp = await client.get("http://127.0.0.1:8103/api/v1/correlate")
            results["spectral"] = resp.json()
        except: results["spectral"] = {"offline": True}

        # Funding pipeline
        try:
            resp = await client.get("http://127.0.0.1:8101/api/v1/pipeline")
            results["funding"] = resp.json()
        except: results["funding"] = {"offline": True}

        # Service status
        try:
            resp = await client.get("http://127.0.0.1:8102/api/v1/status")
            results["status"] = resp.json()
        except: results["status"] = {"offline": True}

    return {"timestamp": int(time.time()), "data": results}
