"""
OpenTelemetry hooks for Game Agent Infra.
Emits spans for every spine append, FSC cycle, and cognition update.
Attributes: ring_estimate, Ω, controlled_reduction, Σf, CS, PS
With graceful fallback when opentelemetry is not installed.
"""

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.sdk.resources import Resource

    # Initialize tracer
    resource = Resource.create({"service.name": "game-agent-infra"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
    HAS_OTEL = True
except ImportError:
    tracer = None
    HAS_OTEL = False


class _noop_context:
    """No-op context manager when OTel is unavailable."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def start_spine_append(agent_id: str, anomaly: str):
    if not HAS_OTEL:
        return _noop_context()
    return tracer.start_as_current_span(
        "spine.append",
        attributes={
            "agent_id": agent_id,
            "anomaly": anomaly,
        },
    )


def start_fsc_cycle(cycle_id: str, ring_estimate: float, omega: float):
    if not HAS_OTEL:
        return _noop_context()
    return tracer.start_as_current_span(
        "fsc.cycle",
        attributes={
            "cycle_id": cycle_id,
            "ring_estimate": ring_estimate,
            "Ω": omega,
        },
    )


def record_cognition_update(agent_id: str, ring_estimate: float, controlled_reduction: float, omega: float, sigma_f: float):
    if not HAS_OTEL:
        return
    with tracer.start_as_current_span("cognition.update") as span:
        span.set_attribute("agent_id", agent_id)
        span.set_attribute("ring_estimate", ring_estimate)
        span.set_attribute("controlled_reduction", controlled_reduction)
        span.set_attribute("Ω", omega)
        span.set_attribute("Σf", sigma_f)


def start_cain_analysis(review_id: str, contradiction_count: int = 0, severity: str = "NONE"):
    """Start span for CAIN Layer 2 adversarial dissent analysis."""
    if not HAS_OTEL:
        return _noop_context()
    return tracer.start_as_current_span(
        "cain.dissent",
        attributes={
            "review_id": review_id,
            "contradictions_found": contradiction_count,
            "severity": severity,
        },
    )


def start_fire_event(title: str, poly_c: float, supercritical: bool = False):
    """Start span for FIRE event creation."""
    if not HAS_OTEL:
        return _noop_context()
    return tracer.start_as_current_span(
        "fire.event",
        attributes={
            "title": title[:100],
            "poly_c": poly_c,
            "supercritical": supercritical,
        },
    )


def start_b1_verification(cycle_id: str, runtime: str, hash_value: str):
    """Start span for B1 cross-runtime verification."""
    if not HAS_OTEL:
        return _noop_context()
    return tracer.start_as_current_span(
        "b1.verify",
        attributes={
            "cycle_id": cycle_id,
            "runtime": runtime,
            "hash_prefix": hash_value[:16],
        },
    )