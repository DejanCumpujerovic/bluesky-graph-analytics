"""Map ORM rows ↔ domain entities."""

from datetime import UTC, datetime

from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.models import FollowRow, ProfileRow


def profile_to_domain(row: ProfileRow) -> Profile:
    return Profile(
        did=DID(row.did),
        handle=Handle(row.handle) if row.handle else None,
        display_name=row.display_name,
        description=row.description,
        followers_count=row.followers_count,
        follows_count=row.follows_count,
        posts_count=row.posts_count,
        detected_language=row.detected_language,
        language_confidence=row.language_confidence or 0.0,
        is_seed=row.is_seed,
    )


def profile_to_row(profile: Profile, *, run_id: int, now: datetime | None = None) -> ProfileRow:
    ts = now or datetime.now(UTC)
    return ProfileRow(
        did=profile.did,
        run_id=run_id,
        handle=profile.handle,
        display_name=profile.display_name,
        description=profile.description,
        followers_count=profile.followers_count,
        follows_count=profile.follows_count,
        posts_count=profile.posts_count,
        detected_language=profile.detected_language,
        language_confidence=profile.language_confidence,
        is_seed=profile.is_seed,
        created_at=ts,
        updated_at=ts,
    )


def follow_to_domain(row: FollowRow) -> FollowRelation:
    return FollowRelation(
        follower_did=DID(row.follower_did),
        followee_did=DID(row.followee_did),
        snapshot_id=SnapshotId(row.snapshot_id),
    )


def follow_to_row(relation: FollowRelation, *, fetched_at: datetime | None = None) -> FollowRow:
    return FollowRow(
        follower_did=relation.follower_did,
        followee_did=relation.followee_did,
        snapshot_id=relation.snapshot_id,
        fetched_at=fetched_at or datetime.now(UTC),
    )
