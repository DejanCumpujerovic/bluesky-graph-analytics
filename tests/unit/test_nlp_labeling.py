"""Community NLP labeling."""

from bluesky_graph_analytics.domain.community.nlp_labeling import (
    community_top_terms,
    preprocess_description,
    profile_language_ok,
)
from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID


def test_preprocess_description() -> None:
    text = "Hello #bluesky https://example.com @user"
    out = preprocess_description(text)
    assert "bluesky" in out
    assert "https" not in out


def test_profile_language_ok_empty() -> None:
    p = Profile(did=DID("did:plc:x"), description=None)
    ok, lang, conf = profile_language_ok(p, threshold=0.9)
    assert not ok
    assert lang == "unknown"


def test_community_top_terms_empty() -> None:
    terms, dist = community_top_terms([], lang_threshold=0.9)
    assert terms == ()
    assert dist == {}


def test_community_top_terms_extracts_words() -> None:
    profiles = [
        Profile(
            did=DID("did:plc:a"),
            description="Graph algorithms and theoretical computer science research",
            detected_language="en",
            language_confidence=0.99,
        ),
        Profile(
            did=DID("did:plc:b"),
            description="Machine learning theory and graph networks in computer science",
            detected_language="en",
            language_confidence=0.99,
        ),
    ]
    terms, dist = community_top_terms(profiles, lang_threshold=0.5, top_n=5)
    assert len(terms) > 0
    assert dist.get("en", 0) >= 1
    joined = " ".join(terms)
    assert "graph" in joined or "computer" in joined or "science" in joined
