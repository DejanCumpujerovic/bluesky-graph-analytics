"""ACL mapper tests."""

from bluesky_graph_analytics.infrastructure.bluesky.acl_mapper import profile_from_atproto


def test_profile_from_atproto() -> None:
    p = profile_from_atproto(
        did="did:plc:abc",
        handle="user.bsky.social",
        display_name="User",
        description="bio",
        followers_count=10,
        is_seed=True,
    )
    assert str(p.did) == "did:plc:abc"
    assert p.is_seed is True
