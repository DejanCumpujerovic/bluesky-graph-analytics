"""Deletion workflow E2E (DEO 8.12 #12)."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from bluesky_graph_analytics.application.records import AnalysisRun, DeletionRecord, RunStatus
from bluesky_graph_analytics.application.services.deletion_service import DeletionService
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyDeletionRepository,
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_deletion_removes_profile_and_follows(
    session_factory: async_sessionmaker,
    db_engine: AsyncEngine,
) -> None:
    runs = SqlAlchemyRunRepository(session_factory)
    profiles = SqlAlchemyProfileRepository(session_factory)
    follows = SqlAlchemyFollowRepository(session_factory)
    deletions = SqlAlchemyDeletionRepository(session_factory)

    snap = SnapshotId("snap_del")
    target = DID("did:plc:target")
    run = (
        await runs.create(
            AnalysisRun(started_at=datetime.now(UTC), snapshot_id=snap, status=RunStatus.COMPLETED)
        )
    ).unwrap()
    assert run.id is not None

    await profiles.upsert(Profile(did=target, is_seed=False), run_id=run.id)
    await follows.save_relations(
        [
            FollowRelation(
                follower_did=target,
                followee_did=DID("did:plc:seed"),
                snapshot_id=snap,
            )
        ]
    )
    await deletions.record(
        DeletionRecord(subject_did=str(target), requested_at=datetime.now(UTC), processed=False)
    )

    count = (await DeletionService(deletions, db_engine).process_pending()).unwrap()
    assert count == 1

    assert (await follows.list_by_snapshot(snap)).unwrap() == []
    prof = (await profiles.get(target, run_id=run.id)).unwrap()
    assert prof is None
