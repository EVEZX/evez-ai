"""
Automated FOIA Monitoring Pipeline for disclosure.tools
Continuously monitors FOIA/UAP sources, ingests new documents,
runs spectral analysis, generates memes, and posts to Discord.
"""
import os
import json
import time
import hashlib
import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx

logger = logging.getLogger("disclosure-monitor")


@dataclass
class MonitoredSource:
    """A FOIA/UAP source being monitored for new documents."""
    id: str
    name: str
    url: str
    last_hash: str = ""
    last_checked: int = 0
    check_count: int = 0
    new_doc_count: int = 0
    enabled: bool = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "url": self.url,
            "last_hash": self.last_hash, "last_checked": self.last_checked,
            "check_count": self.check_count, "new_doc_count": self.new_doc_count,
            "enabled": self.enabled,
        }


@dataclass
class MonitorResult:
    """Result from a monitoring check."""
    source_id: str
    source_name: str
    documents_found: int
    gaps_detected: int
    memes_generated: int
    insight_count: int
    timestamp: int
    changes: bool = False

    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id, "source_name": self.source_name,
            "documents_found": self.documents_found, "gaps_detected": self.gaps_detected,
            "memes_generated": self.memes_generated, "insight_count": self.insight_count,
            "timestamp": self.timestamp, "changes": self.changes,
        }


# Default FOIA/UAP monitoring sources
DEFAULT_SOURCES = [
    {"id": "aaro-official", "name": "AARO Official Site", "url": "https://www.aaro.mil"},
    {"id": "dod-foia", "name": "DoD FOIA Reading Room", "url": "https://www.foia.pentagon.mil"},
    {"id": "archives-uap", "name": "National Archives UAP", "url": "https://www.archives.gov"},
    {"id": "aaro-congressional", "name": "Congressional UAP Reports", "url": "https://www.congress.gov"},
    {"id": "nasa-uap", "name": "NASA UAP Study", "url": "https://www.nasa.gov"},
    {"id": "dia-fires", "name": "DIA FIRE Documents", "url": "https://www.dia.mil"},
    {"id": "faa-uap", "name": "FAA UAP Reports", "url": "https://www.faa.gov"},
    {"id": "navy-uap", "name": "Navy UAP Incidents", "url": "https://www.navy.mil"},
]


class FOIAMonitor:
    """Automated FOIA/UAP source monitor."""

    def __init__(self, data_dir: str = "monitor_data"):
        self.data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), data_dir
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.sources: Dict[str, MonitoredSource] = {}
        self.history: List[MonitorResult] = []
        self.client = httpx.AsyncClient(timeout=30, follow_redirects=True)
        self._load()
        self._init_defaults()

    def _load(self):
        """Load monitor state from disk."""
        state_file = os.path.join(self.data_dir, "state.json")
        if os.path.exists(state_file):
            try:
                data = json.loads(open(state_file).read())
                for s in data.get("sources", []):
                    src = MonitoredSource(
                        id=s["id"], name=s["name"], url=s["url"],
                        last_hash=s.get("last_hash", ""),
                        last_checked=s.get("last_checked", 0),
                        check_count=s.get("check_count", 0),
                        new_doc_count=s.get("new_doc_count", 0),
                        enabled=s.get("enabled", True),
                    )
                    self.sources[src.id] = src
            except Exception as e:
                logger.error(f"Failed to load monitor state: {e}")

    def _save(self):
        """Save monitor state to disk."""
        state_file = os.path.join(self.data_dir, "state.json")
        data = {
            "sources": [s.to_dict() for s in self.sources.values()],
            "history_last": [h.to_dict() for h in self.history[-50:]],
        }
        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    def _init_defaults(self):
        """Add default sources if not already configured."""
        for src in DEFAULT_SOURCES:
            if src["id"] not in self.sources:
                self.sources[src["id"]] = MonitoredSource(
                    id=src["id"], name=src["name"], url=src["url"]
                )
        self._save()

    async def check_source(self, source_id: str) -> Optional[MonitorResult]:
        """Check a single FOIA source for new content."""
        source = self.sources.get(source_id)
        if not source or not source.enabled:
            return None

        try:
            # Fetch the source page
            resp = await self.client.get(source.url)
            content = resp.text
            current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            source.check_count += 1
            source.last_checked = int(time.time())

            # Detect changes
            if source.last_hash and current_hash != source.last_hash:
                changes = True
                source.new_doc_count += 1
            else:
                changes = False

            source.last_hash = current_hash

            # If changes detected, run analysis on the new content
            gaps = 0
            memes = 0
            insights = 0

            if changes:
                try:
                    # Run spectral analysis on the fetched content
                    from gap_detector.ingestion import ingest_text
                    from gap_detector.spectral_engine import SpectralEngine
                    from gap_detector.report import generate_report
                    import numpy as np

                    doc = ingest_text(content, title=source.name, source_type="url")
                    engine = SpectralEngine(operator="evez666")
                    engine.load_corpus([doc.to_corpus_entry()])
                    result = engine.analyze()
                    gaps = result.get("negative_eigenvalues", 0)

                    eigenvalues = np.array(result.get("eigenvalues", []))
                    if eigenvalues.size > 0:
                        report = generate_report(
                            eigenvalues=eigenvalues,
                            n_documents=1,
                            n_sections=len(doc.sections),
                            operator="evez666",
                        )
                        findings = [f.to_dict() for f in report.findings]

                        # Auto-generate memes
                        from meme_factory import auto_generate_memes
                        memes_list = auto_generate_memes(findings)
                        memes = len(memes_list)

                        # Save memes
                        meme_dir = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)), "generated_memes"
                        )
                        os.makedirs(meme_dir, exist_ok=True)
                        for meme in memes_list:
                            svg_path = os.path.join(meme_dir, f"{meme.meme_id}.svg")
                            with open(svg_path, "w") as f:
                                f.write(meme.svg_content)

                    logger.info(f"[{source.name}] Changes detected! Gaps: {gaps}, Memes: {memes}")

                except Exception as e:
                    logger.error(f"Analysis failed for {source.name}: {e}")

            result = MonitorResult(
                source_id=source.id,
                source_name=source.name,
                documents_found=1 if changes else 0,
                gaps_detected=gaps,
                memes_generated=memes,
                insight_count=insights,
                timestamp=int(time.time()),
                changes=changes,
            )
            self.history.append(result)
            self._save()
            return result

        except Exception as e:
            logger.error(f"Check failed for {source.name}: {e}")
            return MonitorResult(
                source_id=source_id,
                source_name=source.name,
                documents_found=0, gaps_detected=0, memes_generated=0,
                insight_count=0, timestamp=int(time.time()),
            )

    async def check_all(self) -> List[MonitorResult]:
        """Check all enabled sources."""
        results = []
        for source_id, source in self.sources.items():
            if source.enabled:
                result = await self.check_source(source_id)
                if result:
                    results.append(result)
        return results

    def get_sources(self) -> List[Dict]:
        """Get all configured sources."""
        return [s.to_dict() for s in self.sources.values()]

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get monitoring history."""
        return [h.to_dict() for h in self.history[-limit:]]

    def add_source(self, name: str, url: str) -> MonitoredSource:
        """Add a new monitoring source."""
        source_id = f"SRC-{hashlib.sha256(f'{name}{url}'.encode()).hexdigest()[:6].upper()}"
        source = MonitoredSource(id=source_id, name=name, url=url)
        self.sources[source_id] = source
        self._save()
        return source

    def toggle_source(self, source_id: str, enabled: bool) -> bool:
        """Enable/disable a source."""
        if source_id in self.sources:
            self.sources[source_id].enabled = enabled
            self._save()
            return True
        return False

    async def close(self):
        await self.client.aclose()


# Singleton
foia_monitor = FOIAMonitor()
