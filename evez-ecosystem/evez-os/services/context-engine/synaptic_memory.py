from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import subprocess
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import networkx as nx


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")


@dataclass
class NodePayload:
    """Canonical node schema stored inside the synaptic graph."""

    node_type: str
    name: str
    source: str
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=lambda: time.time())


class SynapticMemoryGraph:
    """Persistent, self-indexing memory graph for files/functions/actions/API calls."""

    def __init__(
        self,
        graph_path: str | Path = "services/context-engine/data/synaptic_memory.graphml",
        index_path: str | Path = "services/context-engine/data/synaptic_memory_index.json",
        similarity_threshold: float = 0.14,
    ) -> None:
        self.graph_path = Path(graph_path)
        self.index_path = Path(index_path)
        self.similarity_threshold = similarity_threshold
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph = self._load_graph()
        self.token_index = self._load_index()

    def _load_graph(self) -> nx.MultiDiGraph:
        if self.graph_path.exists():
            return nx.read_graphml(self.graph_path)
        return nx.MultiDiGraph()

    def _load_index(self) -> Dict[str, Dict[str, int]]:
        if not self.index_path.exists():
            return {}
        with self.index_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def flush(self) -> None:
        nx.write_graphml(self.graph, self.graph_path)
        with self.index_path.open("w", encoding="utf-8") as f:
            json.dump(self.token_index, f, indent=2, sort_keys=True)

    def upsert_node(self, payload: NodePayload) -> str:
        node_id = self._stable_id(payload.node_type, payload.source, payload.name)
        data = {
            "node_type": payload.node_type,
            "name": payload.name,
            "source": payload.source,
            "content": payload.content[:10000],
            "metadata": json.dumps(payload.metadata, sort_keys=True),
            "ts": str(payload.ts),
        }
        self.graph.add_node(node_id, **data)
        self.token_index[node_id] = dict(self._tokenize(payload.content or payload.name))
        self._connect_semantic_neighbors(node_id)
        return node_id

    def add_relation(
        self,
        source: str,
        target: str,
        relation_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.graph.add_edge(
            source,
            target,
            relation_type=relation_type,
            weight=str(round(weight, 6)),
            metadata=json.dumps(metadata or {}, sort_keys=True),
            ts=str(time.time()),
        )

    def ingest_file(self, path: str | Path, action: str = "read") -> str:
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        file_node = self.upsert_node(
            NodePayload(
                node_type="file",
                name=file_path.name,
                source=str(file_path),
                content=text,
                metadata={"action": action, "size": len(text)},
            )
        )
        if file_path.suffix == ".py":
            for fn_name, lineno in self._extract_functions(text):
                fn_node = self.upsert_node(
                    NodePayload(
                        node_type="function",
                        name=fn_name,
                        source=f"{file_path}:{lineno}",
                        content=f"{fn_name} defined in {file_path}",
                        metadata={"line": lineno},
                    )
                )
                self.add_relation(file_node, fn_node, relation_type="defines", weight=1.0)
        return file_node

    def record_agent_action(self, action: str, detail: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        action_node = self.upsert_node(
            NodePayload(
                node_type="agent_action",
                name=action,
                source=f"agent:{int(time.time()*1000)}",
                content=detail,
                metadata=metadata or {},
            )
        )
        return action_node

    def record_api_call(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
    ) -> str:
        body = json.dumps(payload or {}, sort_keys=True)
        api_node = self.upsert_node(
            NodePayload(
                node_type="api_call",
                name=f"{method.upper()} {endpoint}",
                source=endpoint,
                content=body,
                metadata={"method": method.upper(), "status": response_status},
            )
        )
        return api_node

    def scan_repo(self, root: str | Path = ".") -> int:
        root_path = Path(root)
        count = 0
        for file in root_path.rglob("*"):
            if not file.is_file():
                continue
            if "/.git/" in str(file) or "node_modules" in str(file):
                continue
            if file.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".ts", ".js"}:
                continue
            try:
                self.ingest_file(file, action="scan")
                count += 1
            except Exception:
                continue
        self.flush()
        return count

    def capture_exec(self, cmd: List[str], cwd: str | Path = ".") -> subprocess.CompletedProcess:
        started = time.time()
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        detail = (
            f"cmd={' '.join(cmd)}\n"
            f"returncode={proc.returncode}\n"
            f"stdout={proc.stdout[:4000]}\n"
            f"stderr={proc.stderr[:4000]}"
        )
        node_id = self.record_agent_action(
            action="exec",
            detail=detail,
            metadata={"duration_s": round(time.time() - started, 3)},
        )
        self.add_relation(node_id, node_id, "self_log", 1.0)
        self.flush()
        return proc

    def stats(self) -> Dict[str, Any]:
        types = Counter(self.graph.nodes[n].get("node_type", "unknown") for n in self.graph.nodes)
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_types": dict(types),
            "graph_path": str(self.graph_path),
            "index_path": str(self.index_path),
        }

    def _connect_semantic_neighbors(self, node_id: str) -> None:
        current = self.token_index.get(node_id, {})
        for other_id, other_vec in self.token_index.items():
            if other_id == node_id:
                continue
            score = self._cosine(current, other_vec)
            if score >= self.similarity_threshold:
                self.add_relation(node_id, other_id, "semantic_similarity", score)
                self.add_relation(other_id, node_id, "semantic_similarity", score)

    @staticmethod
    def _stable_id(node_type: str, source: str, name: str) -> str:
        digest = hashlib.sha1(f"{node_type}|{source}|{name}".encode("utf-8")).hexdigest()
        return f"{node_type}:{digest[:16]}"

    @staticmethod
    def _tokenize(text: str) -> Counter:
        return Counter(t.lower() for t in TOKEN_RE.findall(text))

    @staticmethod
    def _cosine(v1: Dict[str, int], v2: Dict[str, int]) -> float:
        if not v1 or not v2:
            return 0.0
        common = set(v1).intersection(v2)
        dot = sum(v1[k] * v2[k] for k in common)
        n1 = math.sqrt(sum(v * v for v in v1.values()))
        n2 = math.sqrt(sum(v * v for v in v2.values()))
        if not n1 or not n2:
            return 0.0
        return dot / (n1 * n2)

    @staticmethod
    def _extract_functions(text: str) -> Iterable[tuple[str, int]]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        functions: List[tuple[str, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append((node.name, int(node.lineno)))
        return functions
