#!/usr/bin/env python3
"""EVEZ Scout — Autonomous research agent using SearXNG"""
import asyncio, json, logging
from typing import List
from pydantic import BaseModel
import httpx
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('evez-scout')

class SearchResult(BaseModel):
    title: str
    content: str = ""
    url: str

class ResearchReport(BaseModel):
    query: str
    results: List[SearchResult]
    summary: str = ""

class ScoutConfig(BaseModel):
    searxng_url: str = "http://127.0.0.1:8888"
    report_output_path: str = "reports"
    max_results: int = 10

async def search(query: str, config: ScoutConfig) -> List[SearchResult]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{config.searxng_url}/search", params={"q": query, "format": "json"})
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("results", [])[:config.max_results]:
            results.append(SearchResult(title=item.get("title", ""), content=item.get("content", "")[:500], url=item.get("url", "")))
        return results

async def research(query: str, config: ScoutConfig) -> ResearchReport:
    log.info(f"Researching: {query}")
    results = await search(query, config)
    return ResearchReport(query=query, results=results, summary=f"Found {len(results)} results")

def load_config(path: str = "config.yaml") -> ScoutConfig:
    with open(path) as f:
        return ScoutConfig(**yaml.safe_load(f))

async def main():
    config = load_config()
    report = await research("EVEZ AI autonomous agents", config)
    print(json.dumps(report.dict(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
