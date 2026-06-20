"""OpenTelemetry tracing helpers (SDK wiring expanded in later slices)."""

from opentelemetry import trace

_tracer = trace.get_tracer("bluesky_graph_analytics")


def get_tracer() -> trace.Tracer:
    return _tracer
