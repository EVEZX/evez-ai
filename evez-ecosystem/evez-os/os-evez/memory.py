#!/usr/bin/env python3
"""
EVEZ-OS Memory System — multi-tier memory for autonomous agents.

Tiers:
    1. Working memory   — in-process dict, fast, volatile
    2. Episodic memory   — full interaction traces stored as JSONL
    3. Semantic memory    — knowledge graph of concepts/repos/agents/capabilities
    4. Long-term memory   — append-only event spine integration
    5. Consolidation      — periodic compression of old events into summaries
"""
import json
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class WorkingMemory:
    """Fast in-process key/value store. Volatile — lost on restart."""

    def __init__(self, max_size: int = 10_000):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._max_size = max_size

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self._max_size and key not in self._store:
                oldest = next(iter(self._store))
                del self._store[oldest]
            self._store[key] = value

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


class EpisodicMemory:
    """
    Stores full interaction traces as JSONL episodes.
    Each episode has an ID, start/end timestamps, and a sequence of events.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self._dir = storage_dir or Path("spine/episodes")
        self._dir.mkdir(parents=True, exist_ok=True)

    def start_episode(self, episode_id: str, metadata: Optional[Dict] = None) -> Path:
        """Begin a new episode trace."""
        path = self._dir / f"{episode_id}.jsonl"
        entry = {
            "kind": "episode.start",
            "episode_id": episode_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        try:
            with open(path, "a") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except OSError:
            pass
        return path

    def record(self, episode_id: str, event_type: str, data: Dict) -> None:
        """Append an event to an episode."""
        path = self._dir / f"{episode_id}.jsonl"
        entry = {
            "kind": event_type,
            "episode_id": episode_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        try:
            with open(path, "a") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def end_episode(self, episode_id: str, summary: Optional[str] = None) -> None:
        """Close an episode."""
        path = self._dir / f"{episode_id}.jsonl"
        entry = {
            "kind": "episode.end",
            "episode_id": episode_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary or "",
        }
        try:
            with open(path, "a") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def read_episode(self, episode_id: str) -> List[Dict]:
        """Read all events from an episode."""
        path = self._dir / f"{episode_id}.jsonl"
        events = []
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return events

    def list_episodes(self) -> List[str]:
        """List all episode IDs."""
        try:
            return sorted(
                p.stem for p in self._dir.glob("*.jsonl")
            )
        except OSError:
            return []


class SemanticMemory:
    """
    Knowledge graph: nodes (concepts, repos, agents, capabilities) with
    typed edges. Persisted as a single JSON file.
    """

    def __init__(self, path: Optional[Path] = None):
        self._path = path or Path("spine/semantic_graph.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._graph = self._load()

    def _load(self) -> Dict:
        try:
            with open(self._path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"nodes": {}, "edges": []}

    def _save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._graph, f, indent=2)
        except OSError:
            pass

    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict] = None,
    ) -> None:
        """Add or update a node in the knowledge graph."""
        with self._lock:
            self._graph["nodes"][node_id] = {
                "type": node_type,
                "properties": properties or {},
                "updated": datetime.now(timezone.utc).isoformat(),
            }
            self._save()

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        properties: Optional[Dict] = None,
    ) -> None:
        """Add a directed edge between nodes."""
        with self._lock:
            edge = {
                "source": source,
                "target": target,
                "relation": relation,
                "properties": properties or {},
            }
            # Avoid duplicates
            for existing in self._graph["edges"]:
                if (
                    existing["source"] == source
                    and existing["target"] == target
                    and existing["relation"] == relation
                ):
                    existing["properties"] = edge["properties"]
                    self._save()
                    return
            self._graph["edges"].append(edge)
            self._save()

    def get_node(self, node_id: str) -> Optional[Dict]:
        with self._lock:
            return self._graph["nodes"].get(node_id)

    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[Dict]:
        """Get all edges from/to a node, optionally filtered by relation."""
        with self._lock:
            results = []
            for edge in self._graph["edges"]:
                if edge["source"] == node_id or edge["target"] == node_id:
                    if relation is None or edge["relation"] == relation:
                        results.append(edge)
            return results

    def search(self, query: str, node_type: Optional[str] = None) -> List[Tuple[str, Dict]]:
        """Simple substring search across node IDs and properties."""
        query_lower = query.lower()
        results = []
        with self._lock:
            for nid, node in self._graph["nodes"].items():
                if node_type and node["type"] != node_type:
                    continue
                searchable = json.dumps({"id": nid, **node}).lower()
                if query_lower in searchable:
                    results.append((nid, node))
        return results

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self._graph["nodes"]:
                return False
            del self._graph["nodes"][node_id]
            self._graph["edges"] = [
                e for e in self._graph["edges"]
                if e["source"] != node_id and e["target"] != node_id
            ]
            self._save()
            return True

    @property
    def node_count(self) -> int:
        return len(self._graph["nodes"])

    @property
    def edge_count(self) -> int:
        return len(self._graph["edges"])


class MemoryConsolidator:
    """
    Periodically compresses old JSONL events into summaries.
    Keeps the spine from growing unbounded.
    """

    def __init__(
        self,
        spine_path: Optional[Path] = None,
        summary_path: Optional[Path] = None,
        max_age_days: int = 7,
    ):
        self._spine_path = spine_path or Path("spine/EVENT_SPINE.jsonl")
        self._summary_path = summary_path or Path("spine/consolidated_summaries.jsonl")
        self._summary_path.parent.mkdir(parents=True, exist_ok=True)
        self._max_age_days = max_age_days

    def consolidate(self) -> Dict[str, Any]:
        """
        Read old events, group by type, produce summaries, append to
        summary log. Returns consolidation report.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._max_age_days)
        old_events = []
        kept_events = []

        try:
            with open(self._spine_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        kept_events.append(line)
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        kept_events.append(line)
                        continue
                    ts_str = event.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            old_events.append(event)
                        else:
                            kept_events.append(line)
                    except (ValueError, AttributeError):
                        kept_events.append(line)
        except FileNotFoundError:
            return {"consolidated": 0, "kept": 0, "error": "spine not found"}

        if not old_events:
            return {"consolidated": 0, "kept": len(kept_events)}

        # Group by event kind
        by_kind: Dict[str, List[Dict]] = {}
        for ev in old_events:
            kind = ev.get("kind", ev.get("event_type", "unknown"))
            by_kind.setdefault(kind, []).append(ev)

        # Write summaries
        summary = {
            "kind": "memory.consolidation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period_start": old_events[0].get("timestamp", ""),
            "period_end": old_events[-1].get("timestamp", ""),
            "total_events": len(old_events),
            "by_kind": {k: len(v) for k, v in by_kind.items()},
            "hash": hashlib.sha256(
                json.dumps(old_events, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest()[:16],
        }

        try:
            with open(self._summary_path, "a") as f:
                f.write(json.dumps(summary, separators=(",", ":")) + "\n")
        except OSError:
            pass

        return {
            "consolidated": len(old_events),
            "kept": len(kept_events),
            "summary": summary,
        }


class MemorySystem:
    """
    Unified memory facade combining all tiers.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        spine_path: Optional[Path] = None,
    ):
        base = base_dir or Path("spine")
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory(base / "episodes")
        self.semantic = SemanticMemory(base / "semantic_graph.json")
        self.consolidator = MemoryConsolidator(
            spine_path=spine_path or (base / "EVENT_SPINE.jsonl"),
            summary_path=base / "consolidated_summaries.jsonl",
        )
        self._spine_path = spine_path or (base / "EVENT_SPINE.jsonl")
        self._spine_path.parent.mkdir(parents=True, exist_ok=True)

    def append_to_spine(self, event: Dict[str, Any]) -> None:
        """Append an event to the long-term event spine."""
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self._spine_path, "a") as f:
                f.write(json.dumps(event, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def read_spine(self, limit: int = 0) -> List[Dict]:
        """Read events from the event spine."""
        events = []
        try:
            with open(self._spine_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        if limit > 0:
            return events[-limit:]
        return events

    def search_spine(self, query: str, limit: int = 50) -> List[Dict]:
        """Simple text search across spine events."""
        query_lower = query.lower()
        results = []
        for event in self.read_spine():
            if query_lower in json.dumps(event).lower():
                results.append(event)
        return results[-limit:]

    def status(self) -> Dict[str, Any]:
        """Return memory system status."""
        return {
            "working_memory_size": self.working.size,
            "episodic_episodes": len(self.episodic.list_episodes()),
            "semantic_nodes": self.semantic.node_count,
            "semantic_edges": self.semantic.edge_count,
            "spine_events": len(self.read_spine()),
        }
