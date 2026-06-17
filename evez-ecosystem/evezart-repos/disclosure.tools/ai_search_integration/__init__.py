"""
AI Search integration for disclosure.tools
Connects to the AI Search Exploitation System for automated corpus ingestion,
real-time FOIA monitoring, and cross-referencing.
"""
import json
import hashlib
import time
import os
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import httpx

# AI Search system endpoints (from the ai-search-exploitation project)
SEARCH_GATEWAY_URL = os.environ.get("SEARCH_GATEWAY_URL", "http://127.0.0.1:8100")
CITATION_ENGINE_URL = os.environ.get("CITATION_ENGINE_URL", "http://127.0.0.1:8101")
KNOWLEDGE_MINER_URL = os.environ.get("KNOWLEDGE_MINER_URL", "http://127.0.0.1:8102")

# UAP/FOIA search operators for Google AI Search
UAP_SEARCH_OPERATORS = {
    "aaro_reports": 'site:defense.gov "AARO" OR "All-domain Anomaly Resolution Office"',
    "foia_uap": 'site:foiaonline.gov OR site:archives.gov "UAP" OR "UFO" OR "unidentified anomalous"',
    "pentagon_uap": 'site:defense.gov "unidentified anomalous phenomena" OR "UAP" after:2024-01-01',
    "navy_uap": 'site:navy.mil "UAP" OR "unidentified" OR "anomalous" filetype:pdf',
    "aaro_classified": 'site:defense.gov "classified" "AARO" OR "UAP task force"',
    "nasa_uap": 'site:nasa.gov "unidentified anomalous phenomena"',
    "congressional_uap": '"UAP" OR "unidentified anomalous" site:congress.gov OR site:senate.gov',
    "foia_releases": '"FOIA release" "UAP" OR "UFO" after:2023-01-01',
    "academic_uap": 'site:scholar.google.com "unidentified anomalous phenomena" OR "UAP detection"',
    "international_uap": '"UAP" OR "unidentified aerial" ("Ministry of Defence" OR "MOD") after:2023-01-01',
}


@dataclass
class FOIASource:
    """A monitored FOIA/UAP source."""
    id: str
    name: str
    url: str
    search_operator: str
    last_checked: int = 0
    last_hash: str = ""
    new_documents: int = 0
    enabled: bool = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "search_operator": self.search_operator,
            "last_checked": self.last_checked,
            "last_hash": self.last_hash,
            "new_documents": self.new_documents,
            "enabled": self.enabled,
        }


@dataclass
class SearchIngestionResult:
    """Result from AI Search ingestion."""
    source_id: str
    query: str
    documents_found: int
    documents_ingested: int
    gaps_detected: int
    timestamp: int

    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "query": self.query,
            "documents_found": self.documents_found,
            "documents_ingested": self.documents_ingested,
            "gaps_detected": self.gaps_detected,
            "timestamp": self.timestamp,
        }


class AISearchIntegration:
    """Integration between disclosure.tools and AI Search Exploitation System."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60)
        self.sources = self._init_sources()
        self.ingestion_history: List[SearchIngestionResult] = []

    def _init_sources(self) -> Dict[str, FOIASource]:
        """Initialize FOIA/UAP search sources."""
        sources = {}
        for idx, (key, operator) in enumerate(UAP_SEARCH_OPERATORS.items()):
            sources[key] = FOIASource(
                id=f"SRC-{hashlib.sha256(key.encode()).hexdigest()[:6].upper()}",
                name=key.replace("_", " ").title(),
                url="https://www.google.com/search",
                search_operator=operator,
            )
        return sources

    async def search_and_ingest(self, source_key: str) -> Optional[SearchIngestionResult]:
        """Search for new UAP/FOIA documents using AI Search and ingest results."""
        source = self.sources.get(source_key)
        if not source or not source.enabled:
            return None

        try:
            # Try the AI Search Gateway first
            resp = await self.client.post(
                f"{SEARCH_GATEWAY_URL}/api/v1/search",
                json={"query": source.search_operator, "max_results": 20},
            )
            if resp.status_code == 200:
                data = resp.json()
                documents = data.get("results", [])
            else:
                # Fallback: direct web search via httpx (limited)
                documents = []

            # Process results through citation engine for credibility
            credible_docs = []
            for doc in documents[:10]:
                try:
                    cite_resp = await self.client.post(
                        f"{CITATION_ENGINE_URL}/api/v1/verify",
                        json={"url": doc.get("url", ""), "content": doc.get("snippet", "")},
                    )
                    if cite_resp.status_code == 200:
                        cite_data = cite_resp.json()
                        if cite_data.get("credibility_tier", 3) <= 2:
                            credible_docs.append(doc)
                except Exception:
                    credible_docs.append(doc)  # Include if citation engine unavailable

            # Run gap analysis on new documents
            gaps = 0
            if credible_docs:
                from gap_detector.spectral_engine import SpectralEngine
                engine = SpectralEngine(operator="evez666")
                engine.load_corpus(credible_docs)
                result = engine.analyze()
                gaps = result.get("negative_eigenvalues", 0)

            # Update source
            source.last_checked = int(time.time())
            source.new_documents = len(credible_docs)

            ingestion = SearchIngestionResult(
                source_id=source.id,
                query=source.search_operator,
                documents_found=len(documents),
                documents_ingested=len(credible_docs),
                gaps_detected=gaps,
                timestamp=int(time.time()),
            )
            self.ingestion_history.append(ingestion)
            return ingestion

        except Exception as e:
            source.last_checked = int(time.time())
            return SearchIngestionResult(
                source_id=source.id,
                query=source.search_operator,
                documents_found=0,
                documents_ingested=0,
                gaps_detected=0,
                timestamp=int(time.time()),
            )

    async def search_all_sources(self) -> List[SearchIngestionResult]:
        """Search all enabled sources."""
        results = []
        for key, source in self.sources.items():
            if source.enabled:
                result = await self.search_and_ingest(key)
                if result:
                    results.append(result)
        return results

    def get_sources(self) -> List[Dict]:
        """Get all configured search sources."""
        return [s.to_dict() for s in self.sources.values()]

    def toggle_source(self, source_key: str, enabled: bool) -> bool:
        """Enable/disable a search source."""
        if source_key in self.sources:
            self.sources[source_key].enabled = enabled
            return True
        return False

    async def close(self):
        await self.client.aclose()


# Singleton
ai_search = AISearchIntegration()
