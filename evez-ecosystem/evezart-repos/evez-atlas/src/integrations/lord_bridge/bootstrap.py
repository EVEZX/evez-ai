from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .registry import registry

log = logging.getLogger(__name__)


@dataclass(slots=True)
class BootstrapResult:
    spine: Any | None = None
    quantum_rng: Any | None = None
    failure_surface_mapper: Any | None = None
    threat_engine: Any | None = None
    bridge_available: bool = False


def bootstrap() -> BootstrapResult:
    result = BootstrapResult()
    log.info('bootstrap starting')

    from spine import Spine
    result.spine = Spine()
    if hasattr(result.spine, 'init'):
        result.spine.init()

    from quantum_rng import QuantumRNG
    result.quantum_rng = QuantumRNG()
    if hasattr(result.quantum_rng, 'seed'):
        result.quantum_rng.seed()

    from fsc import FailureSurfaceMapper
    result.failure_surface_mapper = FailureSurfaceMapper()
    if hasattr(result.failure_surface_mapper, 'map_bounds'):
        result.failure_surface_mapper.map_bounds()

    from threat_engine import ThreatEngine
    result.threat_engine = ThreatEngine()
    if hasattr(result.threat_engine, 'activate'):
        result.threat_engine.activate()

    try:
        from . import lord_bridge  # noqa: F401
        result.bridge_available = True
    except ImportError:
        log.warning('bridge not installed; running standalone')

    log.info('registry ready with %s mutations', len(registry.list_mutations()))
    return result
