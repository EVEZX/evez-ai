"""
FOIA Leaderboard for disclosure.tools
Tracks researchers by gap closure rate and contribution impact.
"""
import json
import hashlib
import time
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Researcher:
    """A FOIA researcher on the leaderboard."""
    id: str
    name: str
    foia_requests: int = 0
    gaps_closed: int = 0
    documents_submitted: int = 0
    analyses_run: int = 0
    score: float = 0.0
    rank: int = 0
    joined_at: int = 0
    last_active: int = 0
    badges: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "foia_requests": self.foia_requests,
            "gaps_closed": self.gaps_closed,
            "documents_submitted": self.documents_submitted,
            "analyses_run": self.analyses_run,
            "score": round(self.score, 2),
            "rank": self.rank,
            "joined_at": self.joined_at,
            "last_active": self.last_active,
            "badges": self.badges,
        }


@dataclass
class FOIARequest:
    """A tracked FOIA request submission."""
    id: str
    researcher_id: str
    agency: str
    description: str
    date_filed: str
    status: str = "pending"  # pending, fulfilled, denied, partial
    gap_closure_count: int = 0
    documents_released: int = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "researcher_id": self.researcher_id,
            "agency": self.agency,
            "description": self.description,
            "date_filed": self.date_filed,
            "status": self.status,
            "gap_closure_count": self.gap_closure_count,
            "documents_released": self.documents_released,
        }


class Leaderboard:
    """FOIA researcher leaderboard management."""

    def __init__(self, data_dir: str = "leaderboard_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.researchers: Dict[str, Researcher] = {}
        self.requests: Dict[str, FOIARequest] = {}
        self._load()

    def _load(self):
        """Load leaderboard data from disk."""
        researchers_file = self.data_dir / "researchers.json"
        if researchers_file.exists():
            try:
                data = json.loads(researchers_file.read_text())
                for r in data:
                    researcher = Researcher(
                        id=r["id"], name=r["name"],
                        foia_requests=r.get("foia_requests", 0),
                        gaps_closed=r.get("gaps_closed", 0),
                        documents_submitted=r.get("documents_submitted", 0),
                        analyses_run=r.get("analyses_run", 0),
                        score=r.get("score", 0.0),
                        joined_at=r.get("joined_at", 0),
                        last_active=r.get("last_active", 0),
                        badges=r.get("badges", []),
                    )
                    self.researchers[researcher.id] = researcher
            except Exception:
                pass

        requests_file = self.data_dir / "requests.json"
        if requests_file.exists():
            try:
                data = json.loads(requests_file.read_text())
                for r in data:
                    req = FOIARequest(
                        id=r["id"], researcher_id=r["researcher_id"],
                        agency=r["agency"], description=r["description"],
                        date_filed=r["date_filed"], status=r.get("status", "pending"),
                        gap_closure_count=r.get("gap_closure_count", 0),
                        documents_released=r.get("documents_released", 0),
                    )
                    self.requests[req.id] = req
            except Exception:
                pass

    def _save(self):
        """Save leaderboard data to disk."""
        (self.data_dir / "researchers.json").write_text(
            json.dumps([r.to_dict() for r in self.researchers.values()], indent=2)
        )
        (self.data_dir / "requests.json").write_text(
            json.dumps([r.to_dict() for r in self.requests.values()], indent=2)
        )

    def _compute_score(self, researcher: Researcher) -> float:
        """Compute leaderboard score: weighted combination of contributions."""
        # Gap closure is the most valuable action
        gap_score = researcher.gaps_closed * 10.0
        # FOIA requests show initiative
        request_score = researcher.foia_requests * 3.0
        # Documents submitted help the corpus
        doc_score = researcher.documents_submitted * 2.0
        # Analyses run show engagement
        analysis_score = min(researcher.analyses_run, 100) * 0.5

        # Bonus: gap closure rate (efficiency)
        if researcher.foia_requests > 0:
            closure_rate = researcher.gaps_closed / researcher.foia_requests
            efficiency_bonus = closure_rate * 5.0
        else:
            efficiency_bonus = 0.0

        return gap_score + request_score + doc_score + analysis_score + efficiency_bonus

    def _update_ranks(self):
        """Recompute rankings after score changes."""
        sorted_researchers = sorted(
            self.researchers.values(), key=lambda r: r.score, reverse=True
        )
        for i, researcher in enumerate(sorted_researchers):
            researcher.rank = i + 1

    def _check_badges(self, researcher: Researcher):
        """Award badges based on milestones."""
        badges = set(researcher.badges)

        if researcher.foia_requests >= 1:
            badges.add("first_request")
        if researcher.foia_requests >= 10:
            badges.add("foia_veteran")
        if researcher.foia_requests >= 50:
            badges.add("foia_machine")
        if researcher.gaps_closed >= 1:
            badges.add("gap_closer")
        if researcher.gaps_closed >= 10:
            badges.add("gap_destroyer")
        if researcher.gaps_closed >= 50:
            badges.add("spectral_hunter")
        if researcher.documents_submitted >= 5:
            badges.add("contributor")
        if researcher.documents_submitted >= 25:
            badges.add("archivist")

        researcher.badges = list(badges)

    def register_researcher(self, name: str) -> Researcher:
        """Register a new researcher."""
        researcher_id = f"R-{hashlib.sha256(name.encode()).hexdigest()[:6].upper()}"
        if researcher_id in self.researchers:
            return self.researchers[researcher_id]

        researcher = Researcher(
            id=researcher_id,
            name=name,
            joined_at=int(time.time()),
            last_active=int(time.time()),
        )
        self.researchers[researcher_id] = researcher
        self._save()
        return researcher

    def record_foia_request(self, researcher_id: str, agency: str,
                            description: str, date_filed: str = "") -> FOIARequest:
        """Record a FOIA request submission."""
        req_id = f"FOIA-{hashlib.sha256(f'{researcher_id}{agency}{time.time()}'.encode()).hexdigest()[:6].upper()}"
        req = FOIARequest(
            id=req_id,
            researcher_id=researcher_id,
            agency=agency,
            description=description,
            date_filed=date_filed or time.strftime("%Y-%m-%d"),
        )
        self.requests[req_id] = req

        if researcher_id in self.researchers:
            self.researchers[researcher_id].foia_requests += 1
            self.researchers[researcher_id].last_active = int(time.time())

        self._update_scores()
        return req

    def record_gap_closure(self, researcher_id: str, count: int = 1):
        """Record gap closures attributed to a researcher."""
        if researcher_id in self.researchers:
            self.researchers[researcher_id].gaps_closed += count
            self.researchers[researcher_id].last_active = int(time.time())
            self._update_scores()

    def record_document_submission(self, researcher_id: str):
        """Record a document corpus contribution."""
        if researcher_id in self.researchers:
            self.researchers[researcher_id].documents_submitted += 1
            self.researchers[researcher_id].last_active = int(time.time())
            self._update_scores()

    def record_analysis(self, researcher_id: str):
        """Record an analysis run."""
        if researcher_id in self.researchers:
            self.researchers[researcher_id].analyses_run += 1
            self.researchers[researcher_id].last_active = int(time.time())
            self._update_scores()

    def _update_scores(self):
        """Recompute all scores and ranks."""
        for researcher in self.researchers.values():
            researcher.score = self._compute_score(researcher)
            self._check_badges(researcher)
        self._update_ranks()
        self._save()

    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        """Get ranked leaderboard."""
        sorted_researchers = sorted(
            self.researchers.values(), key=lambda r: r.score, reverse=True
        )
        return [r.to_dict() for r in sorted_researchers[:limit]]

    def get_researcher(self, researcher_id: str) -> Optional[Dict]:
        """Get researcher details."""
        if researcher_id in self.researchers:
            return self.researchers[researcher_id].to_dict()
        return None

    def get_stats(self) -> Dict:
        """Get leaderboard aggregate stats."""
        return {
            "total_researchers": len(self.researchers),
            "total_requests": len(self.requests),
            "total_gaps_closed": sum(r.gaps_closed for r in self.researchers.values()),
            "total_documents": sum(r.documents_submitted for r in self.researchers.values()),
        }
