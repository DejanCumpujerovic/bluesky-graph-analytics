"""Community and prediction layer integration."""

from pathlib import Path

import pytest
from returns.result import Failure

from bluesky_graph_analytics.application.services.layers.community_layer import (
    CommunityLayerService,
)
from bluesky_graph_analytics.application.services.layers.prediction_layer import (
    PredictionLayerService,
)
from bluesky_graph_analytics.domain.value_objects import SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_community_layer_writes_files(
    session_factory,
    test_settings,
    seeded_run: tuple[SnapshotId, int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, _ = seeded_run
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.layers._common.DATA_DIR",
        str(tmp_path / "data"),
    )
    svc = CommunityLayerService(
        SqlAlchemyRunRepository(session_factory),
        SqlAlchemyFollowRepository(session_factory),
        SqlAlchemyProfileRepository(session_factory),
        test_settings,
    )
    result = await svc.run(snap)
    assert not isinstance(result, Failure)
    out = tmp_path / "data" / "results" / str(snap)
    assert (out / "communities.json").is_file()
    assert (out / "community_stats.csv").is_file()


@pytest.mark.asyncio
async def test_prediction_layer_writes_files(
    session_factory,
    test_settings,
    seeded_run: tuple[SnapshotId, int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, _ = seeded_run
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.layers._common.DATA_DIR",
        str(tmp_path / "data"),
    )
    svc = PredictionLayerService(
        SqlAlchemyRunRepository(session_factory),
        SqlAlchemyFollowRepository(session_factory),
        SqlAlchemyProfileRepository(session_factory),
        test_settings,
    )
    result = await svc.run(snap)
    assert not isinstance(result, Failure)
    out = tmp_path / "data" / "results" / str(snap)
    assert (out / "prediction_results.csv").is_file()
    assert (out / "roc_curves.png").is_file()
