"""Integration tests for list_seeds snapshot filtering (DEO 7 composite profile PK)."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.fixtures.db import create_test_schema

from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_list_seeds_filtered_by_snapshot() -> None:
    engine = await create_test_schema("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    profiles = SqlAlchemyProfileRepository(session_factory)
    follows = SqlAlchemyFollowRepository(session_factory)
    runs = SqlAlchemyRunRepository(session_factory)

    from datetime import UTC, datetime

    snap_a = SnapshotId("snap_a")
    snap_b = SnapshotId("snap_b")

    run_a = (
        await runs.create(
            AnalysisRun(
                started_at=datetime.now(UTC),
                snapshot_id=snap_a,
                status=RunStatus.COMPLETED,
            )
        )
    ).unwrap()
    run_b = (
        await runs.create(
            AnalysisRun(
                started_at=datetime.now(UTC),
                snapshot_id=snap_b,
                status=RunStatus.COMPLETED,
            )
        )
    ).unwrap()
    assert run_a.id is not None and run_b.id is not None

    seed_a = Profile(did=DID("did:plc:seed1"), handle=Handle("seed1.bsky.social"), is_seed=True)
    seed_b = Profile(did=DID("did:plc:seed2"), handle=Handle("seed2.bsky.social"), is_seed=True)
    await profiles.upsert(seed_a, run_id=run_a.id)
    await profiles.upsert(seed_b, run_id=run_b.id)

    await follows.save_relations(
        [
            FollowRelation(
                follower_did=DID("did:plc:f1"),
                followee_did=seed_a.did,
                snapshot_id=snap_a,
            ),
            FollowRelation(
                follower_did=DID("did:plc:f2"),
                followee_did=seed_a.did,
                snapshot_id=snap_b,
            ),
            FollowRelation(
                follower_did=DID("did:plc:f3"),
                followee_did=seed_b.did,
                snapshot_id=snap_b,
            ),
        ]
    )

    listed_a = {p.did for p in (await profiles.list_seeds(snap_a)).unwrap()}
    listed_b = {p.did for p in (await profiles.list_seeds(snap_b)).unwrap()}
    assert listed_a == {seed_a.did}
    # seed_a follow exists in snap_b but profile row is under run_a (snap_a) only
    assert listed_b == {seed_b.did}
    await engine.dispose()
