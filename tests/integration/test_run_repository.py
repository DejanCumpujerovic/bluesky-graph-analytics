"""Run repository: snapshot uniqueness and force resnapshot."""

from datetime import UTC, datetime

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
async def test_force_resnapshot_clears_snapshot_data() -> None:
    engine = await create_test_schema("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    runs = SqlAlchemyRunRepository(session_factory)
    profiles = SqlAlchemyProfileRepository(session_factory)
    follows = SqlAlchemyFollowRepository(session_factory)

    snap = SnapshotId("snap_test")
    run = (
        await runs.create(
            AnalysisRun(started_at=datetime.now(UTC), snapshot_id=snap, status=RunStatus.COMPLETED)
        )
    ).unwrap()
    assert run.id is not None

    seed = Profile(did=DID("did:plc:seed"), handle=Handle("s.bsky.social"), is_seed=True)
    await profiles.upsert(seed, run_id=run.id)
    await follows.save_relations(
        [
            FollowRelation(
                follower_did=DID("did:plc:f1"),
                followee_did=seed.did,
                snapshot_id=snap,
            )
        ]
    )

    assert len((await follows.list_by_snapshot(snap)).unwrap()) == 1

    await runs.force_resnapshot(snap)

    assert (await follows.list_by_snapshot(snap)).unwrap() == []
    assert (await runs.get_by_snapshot_id(snap)).unwrap() is None

    run2 = (
        await runs.create(
            AnalysisRun(started_at=datetime.now(UTC), snapshot_id=snap, status=RunStatus.RUNNING)
        )
    ).unwrap()
    assert run2.id is not None
    await engine.dispose()
