"""Anti-corruption layer: map atproto SDK types → domain models."""

from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle


def profile_from_atproto(
    *,
    did: str,
    handle: str | None,
    display_name: str | None,
    description: str | None = None,
    followers_count: int = 0,
    follows_count: int = 0,
    posts_count: int = 0,
    detected_language: str | None = None,
    language_confidence: float = 0.0,
    is_seed: bool = False,
) -> Profile:
    return Profile(
        did=DID(did),
        handle=Handle(handle) if handle else None,
        display_name=display_name,
        description=description,
        followers_count=followers_count,
        follows_count=follows_count,
        posts_count=posts_count,
        detected_language=detected_language,
        language_confidence=language_confidence,
        is_seed=is_seed,
    )
