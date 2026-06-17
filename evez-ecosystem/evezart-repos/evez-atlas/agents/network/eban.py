"""External Body Area Network (EBAN) digital twin."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class ExternalConnection:
    name: str
    endpoint: str
    last_ping_ms: float
    success_rate: float
    predicted_next_call: float
    bandwidth_budget: float
    weight: float = 0.5
    coactivation_count: int = 0
    last_used_at: datetime = datetime.now(timezone.utc)
    status: str = "ACTIVE"


class EBANDigitalTwin:
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self.connections: dict[str, ExternalConnection] = {
            "github_api": ExternalConnection("github_api", "https://api.github.com", 120, 0.99, 0.8, 1000, last_used_at=now),
            "railway_webhooks": ExternalConnection("railway_webhooks", "https://railway.app/webhooks", 90, 0.97, 0.7, 700, last_used_at=now),
            "prometheus": ExternalConnection("prometheus", "http://prometheus.local:9090", 15, 0.995, 0.9, 1200, last_used_at=now),
            "sse_clients": ExternalConnection("sse_clients", "http://localhost/sse", 10, 0.98, 0.95, 600, last_used_at=now),
        }

    def register_activity(self, active_services: list[str], observed_latency_ms: float) -> None:
        now = datetime.now(timezone.utc)
        for service in active_services:
            conn = self.connections[service]
            conn.last_ping_ms = observed_latency_ms
            conn.last_used_at = now
            conn.success_rate = min(1.0, conn.success_rate + 0.002)
            conn.predicted_next_call = min(1.0, conn.predicted_next_call + 0.02)

        if len(active_services) >= 2:
            for service in active_services:
                conn = self.connections[service]
                conn.coactivation_count += 1
                conn.weight = min(1.0, conn.weight + 0.03)

    def prune_dormant(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now(timezone.utc)
        dormant: list[str] = []
        for name, conn in self.connections.items():
            stale = (now - conn.last_used_at) > timedelta(hours=24)
            low_utility = conn.predicted_next_call < 0.25
            if stale and low_utility:
                conn.status = "DORMANT"
                dormant.append(name)
        return dormant

    def health_map(self) -> dict[str, Any]:
        return {
            "services": [asdict(connection) | {"last_used_at": connection.last_used_at.isoformat()} for connection in self.connections.values()],
            "api_path": "/api/network/eban",
        }
