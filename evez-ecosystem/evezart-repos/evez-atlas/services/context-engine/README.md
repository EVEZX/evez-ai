# context-engine

EVEZ Alpha Layer 2. Sits between `media-ingest` and `context-builder`.

Converts raw multi-source signals (Polymarket, GitHub, arXiv, X) into structured,
temporally-aware, causally-enriched context for the reality simulator.

**Pipeline:** raw signals → signal atoms (capsules) → fused context (graph + vector) → `context.ready` event

**Key insight:** Prediction market Δprob_1h > 8% = `detect_B` event. Market-implied
conditional probabilities weight causal edges in OpenGraph. Resolved markets prune stale edges.

---

## Architecture Position

```
media-ingest
    ↓
context-engine          ← Polymarket, arXiv, GitHub, X
    ├─ signal-detector     (detect_B on velocity spikes)
    ├─ opengraph-db        (causal DAG with market weights)
    ├─ vector DB           (capsule embeddings)
    └─ context.ready → context-builder
```

---

## Signal Sources + Normalization

### Polymarket
```json
{
  "source": "polymarket",
  "event_slug": "btc-200k-2026",
  "question_text": "Will BTC exceed $200k by end of 2026?",
  "yes_prob": 0.31,
  "no_prob": 0.69,
  "volume_24h": 142000,
  "liquidity": 85000,
  "delta_prob_1h": 0.09,
  "resolution_date": "2026-12-31",
  "related_markets": ["btc-150k-2026", "crypto-etf-approval"]
}
```

### arXiv / GitHub
```json
{
  "source": "arxiv",
  "title": "Scalable Oversight via Debate",
  "abstract_chunk": "...",
  "authors": ["Smith J"],
  "timestamp_ms": 1771866396000,
  "embedding": [],
  "tags": ["AI safety", "scalable oversight"],
  "trending_score": 0.82
}
```

---

## Core: ContextEngine Class

```python
# context_engine.py
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

# Constants
EMA_ALPHA = 0.92           # edge weight decay per cycle
MAX_BUFFER = 2000          # rolling capsule buffer
VELOCITY_THRESHOLD = 0.08  # Polymarket delta_prob_1h threshold for detect_B
ENTROPY_CEILING = 0.85     # truth_plane gate
BRIER_PRUNE_THRESHOLD = 0.3  # prune edges with calibration below this


class ContextEngine:
    def __init__(self, vec_db, graph_db, signal_detector):
        self.vec_db = vec_db              # FAISS/Chroma/pgvector
        self.tkg = graph_db              # OpenGraph (Neo4j/FalkorDB)
        self.detector = signal_detector  # DetectB instance (adaptive mode)
        self.buffer: deque = deque(maxlen=MAX_BUFFER)
        self.truth_plane = "CANONICAL"
        self.cycle_count = 0

    def ingest_cycle(self, raw_signals: list) -> dict:
        """Process one scan cycle. Returns cycle summary."""
        self.cycle_count += 1
        capsules = []
        detect_b_events = []

        for sig in raw_signals:
            emb = embedder(sig["text"] or sig.get("question_text", ""))
            capsule = groq_compress(sig)  # LLM: 1-2 sentence + entities + causal hints

            # Market velocity check: delta_prob_1h > threshold = detect_B
            if sig.get("source") == "polymarket" and sig.get("delta_prob_1h"):
                velocity = abs(sig["delta_prob_1h"])
                event = self.detector.process(
                    value=velocity,
                    timestamp_ms=sig.get("timestamp_ms", 0),
                )
                if event["detect_B"]:
                    detect_b_events.append({"signal": sig, "event": event})
                    capsule = self._force_causal_extraction(sig, capsule)

            capsules.append({"capsule": capsule, "emb": emb,
                             "source": sig["source"], "ts": sig.get("timestamp_ms", 0),
                             "meta": sig})

        # Cluster + fuse
        clusters = cluster_embeddings([c["emb"] for c in capsules])
        fused = [fuse_cluster(clust, capsules) for clust in clusters]

        # Update buffer
        self.buffer.extend(fused)

        # Update graph
        for cap in fused:
            node_id = self.tkg.add_or_update_node(cap)
            causal_edges = query_llm_causals(cap)  # Groq/DeepSeek chain
            self._add_causal_edges(node_id, causal_edges)

        # EMA decay all edges
        self._decay_edges()

        # Cross-link markets + papers
        if detect_b_events:
            self._cross_link_correlated(fused)

        # Truth plane gate
        entropy = self._compute_context_entropy(fused)
        if entropy > ENTROPY_CEILING:
            self._reality_reset()  # prune low-confidence subgraph
            self.truth_plane = "DEGRADED"
        else:
            self.truth_plane = "CANONICAL"

        return {
            "cycle": self.cycle_count,
            "capsules_generated": len(fused),
            "detect_b_events": len(detect_b_events),
            "truth_plane": self.truth_plane,
            "entropy": round(entropy, 4),
        }

    def get_context_for_query(self, query_text: str = None,
                               query_emb=None) -> dict:
        """Hybrid retrieve: vector search + graph traversal."""
        emb = query_emb or embedder(query_text)
        vec_hits = self.vec_db.search(emb, k=20, threshold=0.72)
        graph_slice = self.tkg.traverse_from_high_prob_nodes(min_prob=0.5)
        prompt_context = format_as_prompt(vec_hits + graph_slice)
        return {
            "schema": "fused_context/1.0",
            "truth_plane": self.truth_plane,
            "sources": {
                "vector": len(vec_hits),
                "graph": len(graph_slice),
            },
            "prompt_context": prompt_context,
        }

    def simulate_shock(self, intervened_node: str, value: float) -> dict:
        """Counterfactual: set P(node)=value, propagate forward through causal graph."""
        # do-intervention (Pearl do-calculus)
        downstream = self.tkg.get_downstream_nodes(intervened_node)
        posterior = {}
        for node in downstream:
            edge = self.tkg.get_edge(intervened_node, node)
            # Simple forward propagation: P(effect) = P(cause) * edge_weight
            base_prob = self.tkg.get_node_prob(node)
            causal_contribution = value * edge.get("weight", 0.5)
            posterior[node] = min(1.0, base_prob + causal_contribution * (1 - base_prob))
        return {
            "intervention": {"node": intervened_node, "value": value},
            "posterior": posterior,
            "shockable_nodes": [n for n in downstream
                                 if self.tkg.get_node(n).get("shockable", False)],
        }

    def export_snapshot(self, label: str = None) -> dict:
        """Export fused context as a dated artifact (for Gumroad bundles)."""
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        return {
            "schema": "context_snapshot/1.0",
            "label": label or f"Reality Fork {ts[:10]}",
            "timestamp": ts,
            "truth_plane": self.truth_plane,
            "buffer_size": len(self.buffer),
            "graph_nodes": self.tkg.node_count(),
            "graph_edges": self.tkg.edge_count(),
            "capsules": list(self.buffer)[-50:],  # last 50 capsules
            "graphml": self.tkg.export_graphml(),
            "causal_summary": self._generate_causal_narrative(),
        }

    # --- Internal methods ---

    def _force_causal_extraction(self, sig: dict, capsule: str) -> str:
        """On detect_B: force LLM causal extraction for the signal."""
        prompt = (f"Signal: {sig.get('question_text', sig.get('text', ''))}\n"
                  f"Probability velocity: {sig.get('delta_prob_1h', 0):+.1%}\n"
                  f"What prior events caused this? What follows causally? "
                  f"Return: 1 sentence prior, 1 sentence effect, key entities.")
        causal = groq_compress_prompt(prompt)
        return f"{capsule} | CAUSAL: {causal}"

    def _add_causal_edges(self, node_id: str, edges: list) -> None:
        for parent, strength in edges:
            self.tkg.add_edge(
                source=parent, target=node_id,
                weight=strength, type="causal",
                confidence=strength, ttl_cycles=20
            )

    def _decay_edges(self) -> None:
        """EMA decay on all edges. Resolved markets → weight=0 (prune)."""
        for edge in self.tkg.get_all_edges():
            source_market = edge.get("source_market")
            if source_market and source_market.get("resolved"):
                brier = source_market.get("brier_score", 0.5)
                if brier < BRIER_PRUNE_THRESHOLD:
                    self.tkg.remove_edge(edge["id"])
                else:
                    self.tkg.set_edge_weight(edge["id"], 0.0)
            else:
                new_weight = edge.get("weight", 1.0) * EMA_ALPHA
                self.tkg.set_edge_weight(edge["id"], new_weight)

    def _cross_link_correlated(self, capsules: list) -> None:
        """Strengthen edges between correlated capsules (market + paper)."""
        for cap in capsules:
            if cap.get("source") == "arxiv":
                related_markets = self.tkg.find_semantically_related(
                    cap["emb"], node_type="polymarket", k=3
                )
                for market_node, similarity in related_markets:
                    self.tkg.strengthen_edge(
                        source=cap["id"], target=market_node,
                        delta=similarity * 0.1
                    )

    def _compute_context_entropy(self, capsules: list) -> float:
        """Entropy proxy: variance in capsule confidence scores."""
        if not capsules:
            return 0.0
        probs = [c.get("confidence", 0.5) for c in capsules]
        mean = sum(probs) / len(probs)
        variance = sum((p - mean) ** 2 for p in probs) / len(probs)
        return min(1.0, math.sqrt(variance) * 2)

    def _reality_reset(self) -> None:
        """Prune lowest-confidence subgraph to restore coherence."""
        self.tkg.prune_edges_below_confidence(threshold=0.2)
        self.tkg.prune_stale_nodes(max_age_cycles=50)

    def _generate_causal_narrative(self) -> str:
        """LLM: generate 2-3 sentence causal summary of current context."""
        top_nodes = self.tkg.get_top_nodes_by_prob(n=5)
        return groq_compress_prompt(
            f"Causal narrative from these high-probability nodes: {top_nodes}. "
            f"2-3 sentences. Include cause-effect chains and uncertainty."
        )
```

---

## API Endpoints (additions to EVEZ_IMPL.md)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/context-engine/ingest` | Run one scan cycle (submit raw_signals array) |
| POST | `/context-engine/simulate` | Counterfactual shock simulation |
| GET  | `/context-engine/snapshot` | Export dated context snapshot |
| GET  | `/context-engine/entropy` | Current context entropy + truth_plane |
| POST | `/context-engine/reset` | Trigger reality reset (prune) |

---

## Event Bus Topics (additions)

| Topic | Publisher | Subscribers |
|-------|-----------|-------------|
| `market.velocity` | context-engine | signal-detector (detect_B on Δprob) |
| `causal.edge.added` | context-engine | opengraph-db |
| `context.entropy.high` | context-engine | evez-orchestrator (gate synthesis) |
| `context.snapshot` | context-engine | feedback-engine, Gumroad publisher |

---

## Mapping: EVEZ symbolic → context-engine engineering

| EVEZ concept | Engineering equivalent |
|-------------|----------------------|
| "Markets as surface phenomenology" | Polymarket signals as high-frequency detect_B events |
| "Causal graph as noumenal structure" | OpenGraph with market-implied edge weights |
| "Reality fork" | `simulate_shock` counterfactual output |
| "Narrative momentum" | EMA-weighted path strength through causal DAG |
| "Reality reset" | `_reality_reset()` — prune low-confidence subgraph |
| truth_plane CANONICAL | entropy < 0.85, Brier-score calibrated edges |
| truth_plane DEGRADED | entropy ≥ 0.85, synthesis blocked until reset |

---

## Build Order (fits Alpha roadmap)

1. Add `POST /context-engine/ingest` stub to existing API
2. Implement `ingest_cycle` with Polymarket polling (CLOB API or scrape)
3. Wire `delta_prob_1h > 0.08` → `signal_detector.process()` (reuse signal-detector service)
4. Implement `_add_causal_edges` with Groq chain (Groq already connected)
5. Add `simulate_shock` + `export_snapshot` endpoints
6. Wire `context.snapshot` → Gumroad product creation (COMPOSIO: GUMROAD_CREATE_PRODUCT)

---

*context-engine v1.0 — append-only. Canonical reference: docs/architecture/EVEZ_IMPL.md*
