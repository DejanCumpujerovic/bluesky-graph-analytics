import pytest
from pydantic import ValidationError

from bluesky_graph_analytics.domain.models import Community, FollowRelation, LinkPrediction, Profile
from bluesky_graph_analytics.domain.value_objects import (
    DID,
    Handle,
    SimilarityScore,
    SnapshotId,
)


def test_profile_is_frozen() -> None:
    profile = Profile(did=DID("did:plc:example"), handle=Handle("user.bsky.social"))
    with pytest.raises(ValidationError):
        profile.display_name = "x"  # type: ignore[misc]


def test_similarity_score_bounds() -> None:
    score = SimilarityScore(metric_name="overlap", value=0.5, overlap_size=3)
    assert score.value == 0.5
    with pytest.raises(ValidationError):
        SimilarityScore(metric_name="jaccard", value=1.5, overlap_size=0)


def test_follow_relation_snapshot() -> None:
    rel = FollowRelation(
        follower_did=DID("did:plc:a"),
        followee_did=DID("did:plc:b"),
        snapshot_id=SnapshotId("snap_2025_q1"),
    )
    assert rel.snapshot_id == "snap_2025_q1"


def test_community_frozenset_members() -> None:
    community = Community(
        id="c0",
        member_dids=frozenset({DID("did:plc:a"), DID("did:plc:b")}),
        modularity_contribution=0.42,
        top_terms=("topic", "network"),
    )
    assert len(community.member_dids) == 2


def test_link_prediction() -> None:
    pred = LinkPrediction(
        source_did=DID("did:plc:a"),
        target_did=DID("did:plc:b"),
        score=0.8,
        method="common_neighbors",
    )
    assert pred.method == "common_neighbors"
