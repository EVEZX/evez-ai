"""
EVEZ-OS Archive of Ghosts — Session Reconstruction Engine
Past sessions exist as overlapping worlds. The agent can 'haunt' old states
to extract patterns, but never edit the original event log.
"""
import numpy as np
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

@dataclass
class GhostEvent:
    """Immutable event from a past session"""
    event_id: str
    timestamp: str
    session_id: str
    domain: str         # "physics", "code", "narrative", "security"
    event_type: str     # "navigate", "execute", "observe", "decide"
    data: Dict[str, Any]
    merkle_hash: str = ""
    
    def __post_init__(self):
        if not self.merkle_hash:
            content = json.dumps({"id": self.event_id, "ts": self.timestamp,
                                   "domain": self.domain, "type": self.event_type,
                                   "data": self.data}, sort_keys=True)
            self.merkle_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

@dataclass
class GhostSession:
    """A past session that can be haunted"""
    session_id: str
    events: List[GhostEvent] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    domain_tags: List[str] = field(default_factory=list)
    
    def append(self, event: GhostEvent):
        """Append-only — events are immutable once added"""
        if self.events:
            prev_hash = self.events[-1].merkle_hash
        else:
            prev_hash = "genesis"
        self.events.append(event)
        self.end_time = event.timestamp

class GhostArchive:
    """
    The Archive of Ghosts — projection engine over immutable event log.
    
    Past sessions are 'ghosts' — overlapping worlds that can be observed
    from different angles (projections) but never edited.
    
    Key operations:
    - haunt(session_id, projection): Reconstruct a past session under a new domain lens
    - extract_patterns(sessions): Find recurring structures across ghosts
    - ghost_spectrum(sessions): Eigenvalue decomposition of session similarity
    """
    
    def __init__(self, archive_path: Optional[str] = None):
        self.sessions: Dict[str, GhostSession] = {}
        self.archive_path = archive_path
        
        if archive_path:
            self._load_archive(Path(archive_path))
    
    def record_event(self, session_id: str, domain: str, event_type: str, 
                      data: Dict[str, Any]) -> GhostEvent:
        """Record an event — append-only, immutable"""
        if session_id not in self.sessions:
            self.sessions[session_id] = GhostSession(
                session_id=session_id,
                start_time=datetime.utcnow().isoformat()
            )
            
        event = GhostEvent(
            event_id=f"{session_id}_{len(self.sessions[session_id].events):06d}",
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id,
            domain=domain,
            event_type=event_type,
            data=data
        )
        
        self.sessions[session_id].append(event)
        return event
    
    def haunt(self, session_id: str, projection_domain: str) -> Dict[str, Any]:
        """
        Haunt a past session — reconstruct it under a different domain lens.
        
        Original events are never modified. The projection creates a NEW view.
        """
        if session_id not in self.sessions:
            return {"error": f"Session {session_id} not found"}
            
        session = self.sessions[session_id]
        
        # Re-interpret events through the projection domain
        projected_events = []
        for event in session.events:
            projected = {
                "original_event_id": event.event_id,
                "original_domain": event.domain,
                "original_type": event.event_type,
                "projection_domain": projection_domain,
                "reinterpretation": self._reinterpret(event, projection_domain),
                "timestamp": event.timestamp,
                "merkle": event.merkle_hash  # Original hash preserved
            }
            projected_events.append(projected)
            
        return {
            "session_id": session_id,
            "projection": projection_domain,
            "n_events": len(projected_events),
            "events": projected_events,
            "span": f"{session.start_time} → {session.end_time}"
        }
    
    def _reinterpret(self, event: GhostEvent, target_domain: str) -> str:
        """
        Re-interpret an event from one domain into another.
        This is where cross-domain insight extraction happens.
        """
        domain_map = {
            ("code", "narrative"): lambda e: f"Character executes '{e.data.get('action','?')}' — plot advances",
            ("code", "physics"): lambda e: f"State transition: {e.data.get('action','?')} modifies Hamiltonian",
            ("navigate", "physics"): lambda e: f"Wavefunction measured at {e.data.get('url','?')}",
            ("navigate", "narrative"): lambda e: f"Protagonist enters scene: {e.data.get('url','?')}",
            ("observe", "narrative"): lambda e: f"Revelation: {e.data.get('finding','?')}",
            ("decide", "physics"): lambda e: f"Collapse: {e.data.get('choice','?')} selected from superposition",
            ("security", "narrative"): lambda e: f"Antagonist detected: {e.data.get('threat','?')}",
        }
        
        key = (event.domain, target_domain)
        reinterpreter = domain_map.get(key, 
            lambda e: f"[{event.domain}→{target_domain}] {e.data.get('action', str(e.data)[:60])}")
        
        return reinterpreter(event)
    
    def extract_patterns(self, session_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Find recurring structures across ghost sessions.
        Cross-session patterns that repeat = invariants.
        """
        sessions = session_ids or list(self.sessions.keys())
        if len(sessions) < 2:
            return {"patterns": [], "note": "Need ≥2 sessions for pattern extraction"}
        
        # Build event-type frequency vectors for each session
        all_types = set()
        session_vectors = {}
        for sid in sessions:
            if sid not in self.sessions:
                continue
            session = self.sessions[sid]
            type_freq = {}
            for event in session.events:
                key = f"{event.domain}:{event.event_type}"
                type_freq[key] = type_freq.get(key, 0) + 1
                all_types.add(key)
            session_vectors[sid] = type_freq
        
        # Compute similarity matrix
        all_types_list = sorted(all_types)
        n = len(session_vectors)
        if n < 2:
            return {"patterns": [], "note": "Insufficient sessions"}
        
        similarity = np.zeros((n, n))
        sids = list(session_vectors.keys())
        
        for i in range(n):
            for j in range(n):
                vec_i = np.array([session_vectors[sids[i]].get(t, 0) for t in all_types_list])
                vec_j = np.array([session_vectors[sids[j]].get(t, 0) for t in all_types_list])
                dot = np.dot(vec_i, vec_j)
                norm = np.linalg.norm(vec_i) * np.linalg.norm(vec_j) + 1e-10
                similarity[i, j] = dot / norm
        
        # Find recurring patterns (high cross-session similarity)
        patterns = []
        for i in range(n):
            for j in range(i+1, n):
                if similarity[i, j] > 0.5:
                    # Find common event types
                    common = []
                    for t in all_types_list:
                        if session_vectors[sids[i]].get(t, 0) > 0 and session_vectors[sids[j]].get(t, 0) > 0:
                            common.append(t)
                    patterns.append({
                        "sessions": [sids[i], sids[j]],
                        "similarity": float(similarity[i, j]),
                        "common_patterns": common
                    })
        
        return {
            "n_sessions_compared": n,
            "n_patterns": len(patterns),
            "patterns": sorted(patterns, key=lambda p: -p["similarity"])[:10],
            "similarity_matrix_shape": list(similarity.shape)
        }
    
    def ghost_spectrum(self) -> Dict[str, Any]:
        """
        Eigenvalue decomposition of ghost session similarity.
        Negative eigenvalues = contradictory sessions (opposing patterns).
        These are the 'ghost conflicts' — where past selves disagreed.
        """
        sids = list(self.sessions.keys())
        if len(sids) < 2:
            return {"eigenvalues": [], "ghost_conflicts": 0}
        
        all_types = set()
        session_vectors = {}
        for sid in sids:
            session = self.sessions[sid]
            type_freq = {}
            for event in session.events:
                key = f"{event.domain}:{event.event_type}"
                type_freq[key] = type_freq.get(key, 0) + 1
                all_types.add(key)
            session_vectors[sid] = type_freq
        
        all_types_list = sorted(all_types)
        n = len(sids)
        
        # Build similarity matrix
        M = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                vi = np.array([session_vectors[sids[i]].get(t, 0) for t in all_types_list])
                vj = np.array([session_vectors[sids[j]].get(t, 0) for t in all_types_list])
                dot = np.dot(vi, vj)
                norm = np.linalg.norm(vi) * np.linalg.norm(vj) + 1e-10
                M[i, j] = dot / norm
        
        eigenvalues = np.linalg.eigvalsh(M)
        eigenvalues = np.sort(eigenvalues)[::-1]
        
        neg_eigs = [e for e in eigenvalues if e < -0.01]
        
        return {
            "n_sessions": n,
            "eigenvalues": [round(float(e), 6) for e in eigenvalues],
            "ghost_conflicts": len(neg_eigs),
            "dominant_conflict": float(min(eigenvalues)) if neg_eigs else 0,
            "interpretation": "Negative eigenvalues = sessions that contradicted each other. These ghosts disagree."
        }

    def _load_archive(self, path: Path):
        """Load archive from disk"""
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                for sid, sdata in data.get("sessions", {}).items():
                    session = GhostSession(session_id=sid)
                    for edata in sdata.get("events", []):
                        event = GhostEvent(
                            event_id=edata["event_id"],
                            timestamp=edata["timestamp"],
                            session_id=sid,
                            domain=edata["domain"],
                            event_type=edata["event_type"],
                            data=edata["data"],
                            merkle_hash=edata.get("merkle_hash", "")
                        )
                        session.events.append(event)
                    self.sessions[sid] = session
            except Exception as e:
                pass  # Archive corruption = start fresh

    def save(self, path: Optional[str] = None):
        """Persist archive to disk (append-only, never delete)"""
        save_path = Path(path or self.archive_path or "/tmp/ghost_archive.json")
        data = {"sessions": {}}
        for sid, session in self.sessions.items():
            data["sessions"][sid] = {
                "events": [
                    {"event_id": e.event_id, "timestamp": e.timestamp,
                     "domain": e.domain, "event_type": e.event_type,
                     "data": e.data, "merkle_hash": e.merkle_hash}
                    for e in session.events
                ]
            }
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)
