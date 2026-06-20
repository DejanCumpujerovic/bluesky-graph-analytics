"""Shared helpers for analysis layers."""

from pathlib import Path

from returns.result import Failure, Result, Success

from bluesky_graph_analytics.application.ports.run_repository import RunRepository
from bluesky_graph_analytics.application.records import AnalysisRun
from bluesky_graph_analytics.constants import DATA_DIR
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.value_objects import SnapshotId


def results_dir_for(snapshot_id: SnapshotId) -> Path:
    return Path(DATA_DIR) / "results" / str(snapshot_id)


async def resolve_run(
    runs: RunRepository, snapshot_id: SnapshotId
) -> Result[AnalysisRun, DomainError]:
    found = await runs.get_by_snapshot_id(snapshot_id)
    if isinstance(found, Failure):
        return found
    run = found.unwrap()
    if run is None or run.id is None:
        return Failure(
            DomainError(
                code=ErrorCode.NOT_FOUND,
                message=f"No run for snapshot {snapshot_id}; run collect first",
            )
        )
    return Success(run)


async def refresh_run(
    runs: RunRepository, run_id: int, fallback: AnalysisRun
) -> Result[AnalysisRun, DomainError]:
    """Reload run row after layer stats update; use fallback if row missing."""
    found = await runs.get(run_id)
    if isinstance(found, Failure):
        return found
    run = found.unwrap()
    if run is None:
        return Success(fallback)
    return Success(run)
