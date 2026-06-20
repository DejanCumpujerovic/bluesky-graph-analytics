"""NLP helpers for profile language detection (DEO 6.1 analysis.nlp)."""

from langdetect import LangDetectException, detect

from bluesky_graph_analytics.constants import LANGDETECT_DEFAULT_THRESHOLD


def detect_profile_language(
    text: str | None,
    *,
    threshold: float = LANGDETECT_DEFAULT_THRESHOLD,
) -> tuple[str | None, float]:
    if not text or not text.strip():
        return None, 0.0
    try:
        lang = detect(text)
        return lang, threshold
    except LangDetectException:
        return None, 0.0
