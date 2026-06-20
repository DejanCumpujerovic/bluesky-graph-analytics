"""Sentry + health note hooks."""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def configure_observability(*, sentry_dsn: str | None = None) -> None:
    if sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.0)
        logger.info("sentry_initialized")
    else:
        logger.info("sentry_disabled")


def health_notes() -> dict[str, Any]:
    """Lightweight health snapshot for CLI / Streamlit."""
    return {"status": "ok", "component": "bluesky_graph_analytics"}
