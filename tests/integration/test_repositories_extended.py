"""Extended repository coverage."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_list_seeds_and_profiles_for_snapshot(
    session_factory: async_sessionmaker,
    seeded_run: tuple[SnapshotId, int],
) -> None:
    snap, run_id = seeded_run
    profiles = SqlAlchemyProfileRepository(session_factory)
    seeds = (await profiles.list_seeds(snap)).unwrap()
    assert len(seeds) == 2
    all_profiles = (await profiles.list_for_snapshot(snap)).unwrap()
    assert len(all_profiles) >= 3
    got = (await profiles.get(DID("did:plc:s1"), run_id=run_id)).unwrap()
    assert got is not None


@pytest.mark.asyncio
async def test_run_stats_merge(session_factory: async_sessionmaker) -> None:
    runs = SqlAlchemyRunRepository(session_factory)
    snap = SnapshotId("snap_stats")
    run = (
        await runs.create(
            AnalysisRun(started_at=datetime.now(UTC), snapshot_id=snap, status=RunStatus.RUNNING)
        )
    ).unwrap()
    assert run.id is not None
    await runs.merge_stats_section(run.id, "collection", {"seeds_valid": 1})
    await runs.update_stat(run.id, "output_sha256", "abc")
    await runs.finalize_run(run.id, status=RunStatus.COMPLETED)
    refreshed = (await runs.get(run.id)).unwrap()
    assert refreshed is not None
    assert refreshed.stats.get("collection", {}).get("seeds_valid") == 1
