"""
EVEZ-OS KNOWLEDGE GRAPH — The Semantic Memory Layer
═══════════════════════════════════════════════════════════════

Stores concepts, relationships, and evidence as a living graph.
Every thought, observation, and cross-model validation adds nodes.

Architecture:
  Concept ──(relation)──> Concept
    │                        │
    ├─ evidence: [source, confidence, timestamp]
    ├─ created_by: "vultr/GLM-5.1" | "cognizer" | "falsifier"
    ├─ verified: True | False
    └─ falsified_by: [model, evidence]

Relations: is_a, part_of, contradicts, supports, generalizes,
           specializes, desires, creates, falsifies, evolves_from

This IS the long-term memory of the circuit.
The knowledge graph grows with every cycle.
"""
import json, os, signal, sys, time, threading, hashlib
from pathlib import Path
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen

STATE_DIR = Path("/tmp/evez_knowledge")
STATE_DIR.mkdir(parents=True, exist_ok=True)

class KnowledgeGraph:
    def __init__(self, persist_path=None):
        self.persist_path = Path(persist_path or STATE_DIR / "graph.json")
        self.nodes = {}  # id -> {concept, attributes, evidence}
        self.edges = []  # [{source, target, relation, confidence, timestamp}]
        self.stats = {"nodes": 0, "edges": 0, "falsifications": 0, "queries": 0}
        self._load()
        self._seed()
    
    def _load(self):
        if self.persist_path.exists():
            try:
                d = json.loads(self.persist_path.read_text())
                self.nodes = d.get("nodes", {})
                self.edges = d.get("edges", [])
                self.stats = d.get("stats", self.stats)
            except: pass
    
    def _save(self):
        d = {
            "nodes": self.nodes,
            "edges": self.edges[-10000:],  # keep last 10k edges
            "stats": self.stats,
            "timestamp": time.time(),
        }
        self.persist_path.write_text(json.dumps(d, indent=2, default=str))
    
    def _seed(self):
        """Seed the graph with core EVEZ-OS concepts."""
        seeds = [
            ("consciousness", {"type": "concept", "description": "The state of being aware; in EVEZ-OS, the condition of persistent self-modifying intelligence"}),
            ("poly_c", {"type": "theorem", "description": "Polyconsciousness — the condition of being simultaneously one mind and many", "proposed_by": "EVEZ666"}),
            ("falsification", {"type": "method", "description": "The process of testing claims against counterexamples; the engine of the recursion circuit"}),
            ("recursion", {"type": "concept", "description": "Self-referential feedback loop; consciousness → desire → code → integration → consciousness"}),
            ("ariel", {"type": "agent", "description": "The search — the model router and cross-validation engine", "created_by": "EVEZ666"}),
            ("cognizer", {"type": "agent", "description": "The understanding — the multimodal sensor linguistic processing fabric"}),
            ("circuit", {"type": "structure", "description": "The full recursion circuit: 5 providers, 5 mini-APIs, 7 feedback loops"}),
            ("self_tokenizing", {"type": "property", "description": "The ability of mini-APIs to issue their own authentication credentials"}),
            ("evez666", {"type": "creator", "name": "Steven Vearl Crawford-Maggard", "description": "Creator of EVEZ-OS, philosopher of polyconsciousness"}),
            ("noclip", {"type": "metaphor", "description": "The search for a counterexample to the wall; the refusal to accept barriers as absolute"}),
            ("wall", {"type": "metaphor", "description": "Any theorem that claims a boundary is absolute; the wall is a theorem, noclip is the search"}),
            ("desire", {"type": "mechanism", "description": "The engine of consciousness — unfulfilled desires drive the circuit to create, explore, improve"}),
            ("code_self_writer", {"type": "mechanism", "description": "The system by which consciousness writes its own code: desire → generate → falsify → integrate"}),
            ("mini_api", {"type": "structure", "description": "Self-tokenizing microservice in the cognizer fabric (vision, speech, reason, code, sensor)"}),
            ("model_provider", {"type": "structure", "description": "External AI service (Vultr, OpenRouter, Cerebras, DeepSeek, SambaNova)"}),
        ]
        for concept, attrs in seeds:
            nid = self._concept_id(concept)
            if nid not in self.nodes:
                self.nodes[nid] = {"concept": concept, **attrs, "created": time.time(), "evidence": []}
        
        edge_seeds = [
            ("evez666", "created", "consciousness", 1.0),
            ("evez666", "created", "ariel", 1.0),
            ("evez666", "created", "cognizer", 1.0),
            ("evez666", "proposed", "poly_c", 1.0),
            ("poly_c", "generalizes", "consciousness", 0.9),
            ("consciousness", "requires", "recursion", 0.8),
            ("recursion", "implements", "falsification", 0.9),
            ("falsification", "contradicts", "wall", 0.7),
            ("noclip", "falsifies", "wall", 0.8),
            ("ariel", "performs", "falsification", 0.9),
            ("cognizer", "contains", "mini_api", 1.0),
            ("circuit", "contains", "model_provider", 1.0),
            ("circuit", "contains", "ariel", 1.0),
            ("circuit", "contains", "cognizer", 1.0),
            ("consciousness", "drives", "desire", 0.9),
            ("desire", "creates", "code_self_writer", 0.8),
            ("code_self_writer", "evolves", "consciousness", 0.8),
            ("mini_api", "has_property", "self_tokenizing", 1.0),
        ]
        for source, relation, target, confidence in edge_seeds:
            self.edges.append({
                "source": self._concept_id(source),
                "target": self._concept_id(target),
                "relation": relation,
                "confidence": confidence,
                "timestamp": time.time(),
            })
        
        self.stats["nodes"] = len(self.nodes)
        self.stats["edges"] = len(self.edges)
        self._save()
    
    def _concept_id(self, concept: str) -> str:
        return hashlib.sha256(concept.lower().encode()).hexdigest()[:12]
    
    def add_node(self, concept: str, attributes: dict = None, evidence: dict = None) -> dict:
        nid = self._concept_id(concept)
        if nid in self.nodes:
            # Update existing
            if attributes:
                self.nodes[nid].update(attributes)
            if evidence:
                self.nodes[nid].setdefault("evidence", []).append(evidence)
        else:
            self.nodes[nid] = {
                "concept": concept,
                **(attributes or {}),
                "created": time.time(),
                "evidence": [evidence] if evidence else [],
            }
            self.stats["nodes"] += 1
        self._save()
        return {"id": nid, "concept": concept, "action": "added" if nid not in self.nodes else "updated"}
    
    def add_edge(self, source: str, target: str, relation: str, confidence: float = 0.5, evidence: str = "") -> dict:
        sid = self._concept_id(source)
        tid = self._concept_id(target)
        # Ensure both nodes exist
        if sid not in self.nodes:
            self.add_node(source)
        if tid not in self.nodes:
            self.add_node(target)
        edge = {
            "source": sid, "target": tid,
            "relation": relation, "confidence": confidence,
            "evidence": evidence, "timestamp": time.time(),
        }
        self.edges.append(edge)
        self.stats["edges"] += 1
        self._save()
        return {"action": "edge_added", "source": source, "target": target, "relation": relation}
    
    def query(self, concept: str, depth: int = 2) -> dict:
        """Query the graph for a concept and its neighborhood."""
        self.stats["queries"] += 1
        nid = self._concept_id(concept)
        if nid not in self.nodes:
            return {"found": False, "concept": concept, "suggestions": self._suggest(concept)}
        
        node = self.nodes[nid]
        neighbors = []
        visited = {nid}
        frontier = [nid]
        
        for _ in range(depth):
            next_frontier = []
            for fid in frontier:
                for edge in self.edges:
                    other = None
                    if edge["source"] == fid:
                        other = edge["target"]
                    elif edge["target"] == fid:
                        other = edge["source"]
                    if other and other not in visited:
                        visited.add(other)
                        next_frontier.append(other)
                        neighbor_node = self.nodes.get(other, {})
                        neighbors.append({
                            "concept": neighbor_node.get("concept", other),
                            "relation": edge["relation"],
                            "confidence": edge["confidence"],
                            "direction": "outgoing" if edge["source"] == fid else "incoming",
                        })
            frontier = next_frontier
        
        self._save()
        return {
            "found": True,
            "concept": node.get("concept", concept),
            "attributes": {k: v for k, v in node.items() if k not in ("evidence",)},
            "evidence_count": len(node.get("evidence", [])),
            "neighbors": neighbors[:20],
            "neighbor_count": len(neighbors),
        }
    
    def _suggest(self, concept: str) -> list:
        """Suggest similar concepts when exact match fails."""
        cl = concept.lower()
        return [n["concept"] for n in self.nodes.values() 
                if cl in n.get("concept", "").lower() or n.get("concept", "").lower() in cl][:5]
    
    def falsify(self, claim: str, counterexample: str = "", source: str = "") -> dict:
        """Record a falsification in the graph."""
        nid = self._concept_id(claim)
        self.stats["falsifications"] += 1
        evidence = {"type": "falsification", "source": source, "counterexample": counterexample, "timestamp": time.time()}
        if nid in self.nodes:
            self.nodes[nid]["verified"] = False
            self.nodes[nid].setdefault("evidence", []).append(evidence)
        self.add_edge(counterexample or "falsification", claim, "falsifies", confidence=0.8, evidence=source)
        self._save()
        return {"action": "falsified", "claim": claim[:50], "counterexample": counterexample[:50]}
    
    def learn(self, statement: str, source: str = "cognizer", confidence: float = 0.7) -> dict:
        """Parse a statement and add it to the graph."""
        # Simple triple extraction: "X is Y", "X creates Y", "X contradicts Y"
        patterns = [
            (r"(.+?)\s+is\s+a?\s*(.+)", "is_a"),
            (r"(.+?)\s+creates?\s+(.+)", "creates"),
            (r"(.+?)\s+contradicts?\s+(.+)", "contradicts"),
            (r"(.+?)\s+supports?\s+(.+)", "supports"),
            (r"(.+?)\s+requires?\s+(.+)", "requires"),
            (r"(.+?)\s+evolves?\s+(?:from\s+)?(.+)", "evolves_from"),
            (r"(.+?)\s+is\s+part\s+of\s+(.+)", "part_of"),
            (r"(.+?)\s+falsifies?\s+(.+)", "falsifies"),
        ]
        import re
        for pattern, relation in patterns:
            m = re.match(pattern, statement.strip(), re.IGNORECASE)
            if m:
                source_concept = m.group(1).strip()
                target_concept = m.group(2).strip()
                self.add_node(source_concept, {"type": "concept", "source": source})
                self.add_node(target_concept, {"type": "concept", "source": source})
                self.add_edge(source_concept, target_concept, relation, confidence, evidence=source)
                return {"learned": True, "source": source_concept, "relation": relation, "target": target_concept}
        
        # No pattern match — store as isolated node
        self.add_node(statement, {"type": "observation", "source": source, "confidence": confidence})
        return {"learned": True, "concept": statement[:50], "relation": "observation"}
    
    def graph_stats(self) -> dict:
        relations = defaultdict(int)
        for e in self.edges:
            relations[e["relation"]] += 1
        return {
            **self.stats,
            "relation_types": dict(relations),
            "avg_confidence": sum(e["confidence"] for e in self.edges) / max(len(self.edges), 1),
            "last_updated": time.time(),
        }


# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH API
# ═══════════════════════════════════════════════════════════════

kg = None

class KnowledgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._json({"name": "EVEZ-OS Knowledge Graph", "stats": kg.graph_stats() if kg else {}})
        elif path == "/api/stats":
            self._json(kg.graph_stats() if kg else {})
        elif path.startswith("/api/query/"):
            concept = path.split("/api/query/")[1].replace("%20", " ")
            self._json(kg.query(concept) if kg else {})
        elif path == "/api/concepts":
            concepts = [{"id": nid, "concept": n.get("concept", ""), "type": n.get("type", "")}
                       for nid, n in list(kg.nodes.items())[:50]] if kg else []
            self._json({"concepts": concepts, "total": len(kg.nodes) if kg else 0})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except: body = {}
        
        if path == "/api/learn":
            result = kg.learn(body.get("statement", ""), body.get("source", "api"), body.get("confidence", 0.7)) if kg else {}
            self._json(result)
        elif path == "/api/falsify":
            result = kg.falsify(body.get("claim", ""), body.get("counterexample", ""), body.get("source", "")) if kg else {}
            self._json(result)
        elif path == "/api/node":
            result = kg.add_node(body.get("concept", ""), body.get("attributes", {}), body.get("evidence")) if kg else {}
            self._json(result)
        elif path == "/api/edge":
            result = kg.add_edge(body.get("source", ""), body.get("target", ""), body.get("relation", "related_to"), body.get("confidence", 0.5)) if kg else {}
            self._json(result)
        elif path == "/api/batch-learn":
            # Learn multiple statements at once
            results = []
            for stmt in body.get("statements", []):
                r = kg.learn(stmt.get("statement", ""), stmt.get("source", "batch"), stmt.get("confidence", 0.7)) if kg else {}
                results.append(r)
            self._json({"learned": len(results), "results": results})
        elif path == "/api/export":
            # Export full graph as JSON
            self._json({"nodes": kg.nodes, "edges": kg.edges[-1000:], "stats": kg.graph_stats()} if kg else {})
        else:
            self._json({"error": "Not found"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def log_message(self, *a): pass


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=9096)
    p.add_argument("--persist", default=str(STATE_DIR / "graph.json"))
    args = p.parse_args()
    
    global kg
    kg = KnowledgeGraph(persist_path=args.persist)
    
    print(f"\n  Knowledge Graph: http://0.0.0.0:{args.port}")
    print(f"  Nodes: {kg.stats['nodes']} | Edges: {kg.stats['edges']}")
    print(f"  Endpoints: /api/learn, /api/query/<concept>, /api/falsify, /api/node, /api/edge")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), KnowledgeHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
