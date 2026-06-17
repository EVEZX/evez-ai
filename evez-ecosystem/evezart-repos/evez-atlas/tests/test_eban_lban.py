from datetime import datetime, timedelta, timezone

from agents.network.eban import EBANDigitalTwin
from agents.network.lban import LBANDigitalTwin
from agents.solve.precompute import PrecomputeEngine


def test_eban_marks_dormant_nodes():
    twin = EBANDigitalTwin()
    stale = datetime.now(timezone.utc) - timedelta(hours=25)
    twin.connections["github_api"].last_used_at = stale
    twin.connections["github_api"].predicted_next_call = 0.1
    dormant = twin.prune_dormant(now=datetime.now(timezone.utc))
    assert "github_api" in dormant
    assert twin.connections["github_api"].status == "DORMANT"


def test_lban_ltp_increases_myelination():
    lban = LBANDigitalTwin()
    key = ("identity_core", "consciousness_core")
    before = lban.links[key].myelination_factor
    lban.register_signal(*key)
    after = lban.links[key].myelination_factor
    assert round(after - before, 3) == 0.01


def test_precompute_cache_hit_rate_exceeds_50_percent():
    lban = LBANDigitalTwin()
    # strengthen a link so priority path is explicit
    for _ in range(20):
        lban.register_signal("temporal_spine", "latency_pipeline")

    engine = PrecomputeEngine(lban=lban)
    base_problem = {
        "operation_type": "sum",
        "input_shape": "3",
        "context_embedding": "latency",
        "payload": [1, 2, 3],
    }

    # warm cache
    engine.request(base_problem)

    # repeated requests should hit cache more than half the time
    for _ in range(20):
        engine.request(base_problem)

    assert engine.cache_hit_rate() > 0.5
