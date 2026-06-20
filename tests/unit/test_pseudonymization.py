import pytest

from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle
from bluesky_graph_analytics.infrastructure.pseudonymization import Pseudonymizer


def test_blake2b_pseudonym_deterministic() -> None:
    salt = b"x" * 32
    p = Pseudonymizer(salt)
    did = DID("did:plc:abc")
    assert p.hash_did(did) == p.hash_did(did)
    assert len(p.hash_did(did)) == 16


def test_anonymize_profile_strips_display_fields() -> None:
    salt = b"y" * 32
    p = Pseudonymizer(salt)
    profile = Profile(
        did=DID("did:plc:abc"),
        handle=Handle("user.bsky.social"),
        display_name="Name",
        description="Bio",
    )
    out = p.anonymize_profile(profile)
    assert out["display_name"] is None
    assert out["description"] is None
    assert out["did"] != "did:plc:abc"


def test_salt_min_length() -> None:
    with pytest.raises(ValueError):
        Pseudonymizer(b"short")
