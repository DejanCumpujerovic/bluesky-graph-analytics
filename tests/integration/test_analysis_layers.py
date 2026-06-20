"""Analysis layer integration on seeded DB."""

from pathlib import Path

import pytest
from returns.result import Failure

from bluesky_graph_analytics.application.services.layers._common import results_dir_for
from bluesky_graph_analytics.application.services.layers.similarity_layer import (
    SimilarityLayerService,
)
from bluesky_graph_analytics.domain.value_objects import SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_similarity_layer_writes_outputs(
    session_factory,
    test_settings,
    seeded_run: tuple[SnapshotId, int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, _ = seeded_run
    data_root = tmp_path / "data"
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.layers._common.DATA_DIR",
        str(data_root),
    )

    svc = SimilarityLayerService(
        SqlAlchemyRunRepository(session_factory),
        SqlAlchemyFollowRepository(session_factory),
        SqlAlchemyProfileRepository(session_factory),
        test_settings,
    )
    result = await svc.run(snap)
    assert not isinstance(result, Failure)

    out_dir = results_dir_for(snap)
    assert (out_dir / "similarity_jaccard.parquet").is_file()
    assert (out_dir / "top_pairs.csv").is_file()
    assert (out_dir / "metric_correlation.csv").is_file()
