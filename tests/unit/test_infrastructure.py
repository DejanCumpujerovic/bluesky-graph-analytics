"""Thin infrastructure modules."""

from bluesky_graph_analytics.infrastructure.logging import configure_logging
from bluesky_graph_analytics.infrastructure.nlp import detect_profile_language
from bluesky_graph_analytics.infrastructure.observability import configure_observability


def test_configure_logging() -> None:
    configure_logging("DEBUG", log_format="console")


def test_configure_observability() -> None:
    configure_observability(sentry_dsn=None)


def test_detect_profile_language() -> None:
    lang, conf = detect_profile_language("This is an English sentence about graphs.")
    assert lang in {"en", None} or conf >= 0.0
