"""GNN optimizer for the EvezBrain WBAN topology."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from agents.core.event_bus import GLOBAL_EVENT_BUS

try:
    from torch_geometric.nn import SAGEConv  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without torch_geometric
    class SAGEConv(nn.Module):
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.linear = nn.Linear(in_channels, out_channels)

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            src, dst = edge_index
            agg = torch.zeros_like(x)
            agg.index_add_(0, dst, x[src])
            deg = torch.zeros(x.size(0), device=x.device)
            deg.index_add_(0, dst, torch.ones(dst.size(0), device=x.device))
            deg = deg.clamp_min(1.0).unsqueeze(1)
            return self.linear((x + agg / deg) / 2)


NODE_NAMES = ["memory", "consciousness", "identity", "survival", "latency", "temporal"]


@dataclass
class SignalEdge:
    source: str
    target: str
    bandwidth_hz: float
    latency_ms: float
    trust_score: float
    synaptic_strength: float


class WBANGraphModel(nn.Module):
    def __init__(self, in_channels: int = 4, hidden: int = 16, out_channels: int = 8):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden)
        self.conv2 = SAGEConv(hidden, out_channels)
        self.edge_mlp = nn.Sequential(
            nn.Linear(out_channels * 2, 16),
            nn.ReLU(),
            nn.Linear(16, 2),
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = F.relu(self.conv1(x, edge_index))
        emb = self.conv2(x, edge_index)
        src, dst = edge_index
        edge_emb = torch.cat([emb[src], emb[dst]], dim=1)
        updates = self.edge_mlp(edge_emb)
        return emb, updates


class GNNWBANOptimizer:
    def __init__(self, topology_path: str = "dashboard/gnn_topology.json"):
        self.model = WBANGraphModel()
        self.learning_rate = 0.01
        self.topology_path = Path(topology_path)
        self.last_run: datetime | None = None
        self.edge_list = self._build_default_edges()

    def _build_default_edges(self) -> list[SignalEdge]:
        edges: list[SignalEdge] = []
        for idx, source in enumerate(NODE_NAMES):
            target = NODE_NAMES[(idx + 1) % len(NODE_NAMES)]
            edges.append(
                SignalEdge(
                    source=source,
                    target=target,
                    bandwidth_hz=120 + idx * 10,
                    latency_ms=7 + idx,
                    trust_score=0.6 + idx * 0.05,
                    synaptic_strength=0.5 + idx * 0.06,
                )
            )
        return edges

    def _tensorize(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        node_feats = []
        for node in NODE_NAMES:
            node_edges = [e for e in self.edge_list if e.source == node or e.target == node]
            mean_bandwidth = sum(e.bandwidth_hz for e in node_edges) / len(node_edges)
            mean_latency = sum(e.latency_ms for e in node_edges) / len(node_edges)
            mean_trust = sum(e.trust_score for e in node_edges) / len(node_edges)
            mean_synaptic = sum(e.synaptic_strength for e in node_edges) / len(node_edges)
            node_feats.append([mean_bandwidth / 200, mean_latency / 20, mean_trust, mean_synaptic])

        edge_index = torch.tensor(
            [[NODE_NAMES.index(e.source) for e in self.edge_list], [NODE_NAMES.index(e.target) for e in self.edge_list]],
            dtype=torch.long,
        )
        edge_attr = torch.tensor(
            [[e.bandwidth_hz, e.latency_ms, e.trust_score, e.synaptic_strength] for e in self.edge_list],
            dtype=torch.float32,
        )
        return torch.tensor(node_feats, dtype=torch.float32), edge_index, edge_attr

    def train(self, epochs: int = 20) -> list[float]:
        x, edge_index, edge_attr = self._tensorize()
        losses: list[float] = []
        for _ in range(epochs):
            self.model.zero_grad()
            _, updates = self.model(x, edge_index)
            latency_pred = torch.sigmoid(updates[:, 0]) * 15
            coherence_pred = torch.sigmoid(updates[:, 1])
            target_latency = edge_attr[:, 1] * 0.8
            target_coherence = torch.clamp(edge_attr[:, 3] + 0.1, max=1.0)
            loss = F.mse_loss(latency_pred, target_latency) + F.mse_loss(coherence_pred, target_coherence)
            loss.backward()
            with torch.no_grad():
                for param in self.model.parameters():
                    if param.grad is not None:
                        param -= self.learning_rate * param.grad
            losses.append(float(loss.item()))
        return losses

    def optimize_and_emit(self) -> dict[str, Any]:
        self.train(epochs=20)
        x, edge_index, _ = self._tensorize()
        _, updates = self.model(x, edge_index)
        for edge, upd in zip(self.edge_list, updates.detach()):
            edge.latency_ms = max(1.0, edge.latency_ms * (0.9 + float(torch.sigmoid(upd[0])) * 0.1))
            edge.synaptic_strength = min(1.0, edge.synaptic_strength + float(torch.sigmoid(upd[1])) * 0.05)
            edge.trust_score = min(1.0, edge.trust_score + 0.01)

        payload = {
            "nodes": [{"id": name} for name in NODE_NAMES],
            "edges": [asdict(e) for e in self.edge_list],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.topology_path.parent.mkdir(parents=True, exist_ok=True)
        self.topology_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        GLOBAL_EVENT_BUS.emit("wban.topology.updated", payload)
        self.last_run = datetime.now(timezone.utc)
        return payload

    def maybe_run_scheduler(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self.last_run is None or (now - self.last_run) >= timedelta(minutes=5):
            self.optimize_and_emit()
            return True
        return False
