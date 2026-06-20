"""Analysis service orchestration."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from returns.result import Failure, Success

from bluesky_graph_analytics.application.dto import AnalysisRequestDTO
from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.application.services.analysis_service import AnalysisService
from bluesky_graph_analytics.domain.value_objects import SnapshotId


@pytest.mark.asyncio
async def test_run_all_merges_output_hash(
    test_settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap = SnapshotId("snap_x")
    run = AnalysisRun(
        id=1,
        started_at=datetime.now(UTC),
        snapshot_id=snap,
        status=RunStatus.COMPLETED,
    )

    runs = MagicMock()
    runs.get = AsyncMock(return_value=Success(run))
    runs.update_stat = AsyncMock(return_value=Success(None))
    runs.finalize_run = AsyncMock(return_value=Success(None))

    layer = MagicMock()
    layer.run = AsyncMock(return_value=Success(run))

    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.analysis_service.results_dir_for",
        lambda _s: tmp_path,
    )
    (tmp_path / "out.csv").write_text("x", encoding="utf-8")

    svc = AnalysisService(runs, layer, layer, layer, test_settings)
    result = await svc.run_all(AnalysisRequestDTO(snapshot_id=snap))
    assert not isinstance(result, Failure)
    assert result.unwrap().id == 1
    runs.update_stat.assert_called_once()
