"""Export service integration."""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from bluesky_graph_analytics.application.dto import ExportRequestDTO
from bluesky_graph_analytics.application.services.export_service import ExportService
from bluesky_graph_analytics.application.services.layers._common import results_dir_for
from bluesky_graph_analytics.domain.value_objects import SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import (
    SqlAlchemyFollowRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyRunRepository,
)


@pytest.mark.asyncio
async def test_export_anonymized_zip(
    session_factory: async_sessionmaker,
    test_settings,
    seeded_run: tuple[SnapshotId, int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, _run_id = seeded_run
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.export_service.DATA_DIR",
        str(tmp_path / "data"),
    )
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.layers._common.DATA_DIR",
        str(tmp_path / "data"),
    )

    results = results_dir_for(snap)
    results.mkdir(parents=True, exist_ok=True)
    (results / "prediction_results.csv").write_text("method,auc\nx,0.5\n", encoding="utf-8")

    runs = SqlAlchemyRunRepository(session_factory)
    run = (await runs.get_by_snapshot_id(snap)).unwrap()
    assert run is not None
    run = run.model_copy(update={"config_snapshot": "seed: 42", "git_commit_hash": "abc"})
    # config_snapshot is on create only — update via repository if needed

    svc = ExportService(
        SqlAlchemyProfileRepository(session_factory),
        SqlAlchemyFollowRepository(session_factory),
        runs,
        test_settings,
    )
    out = (
        await svc.export(
            ExportRequestDTO(snapshot_id=snap, anonymized=True, output=str(tmp_path / "out.zip"))
        )
    ).unwrap()

    assert out.is_file()
    import zipfile

    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "profiles.parquet" in names
        manifest = zf.read("manifest.json").decode()
        assert "pseudonym_salt_fingerprint" in manifest
