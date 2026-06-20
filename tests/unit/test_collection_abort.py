"""Collection abort when no valid seeds."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from returns.result import Failure, Success

from bluesky_graph_analytics.application.dto import CollectRequestDTO
from bluesky_graph_analytics.application.services.collection_service import CollectionService
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.seeds.seed_file import SeedEntry, SeedFile
from bluesky_graph_analytics.domain.value_objects import Handle, SnapshotId
from bluesky_graph_analytics.infrastructure.persistence.repositories import SqlAlchemyRunRepository


@pytest.mark.asyncio
async def test_collect_aborts_when_no_valid_seeds(
    session_factory,
    test_settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bluesky_graph_analytics.application.services.collection_service.load_seed_file",
        lambda _s: Success(
            SeedFile(seeds=[SeedEntry(handle=Handle("bad.bsky.social"), topic="t")])
        ),
    )

    bluesky = MagicMock()
    bluesky.resolve_handle = AsyncMock(
        return_value=Failure(DomainError(code=ErrorCode.EXTERNAL_API, message="not found"))
    )

    deletions = MagicMock()
    deletions.load_deleted_set = AsyncMock(return_value=Success(frozenset()))

    svc = CollectionService(
        bluesky,
        MagicMock(),
        MagicMock(),
        deletions,
        SqlAlchemyRunRepository(session_factory),
        test_settings,
    )
    result = await svc.collect(
        CollectRequestDTO(
            seed_handles=[Handle("bad.bsky.social")],
            snapshot_id=SnapshotId("snap_empty"),
        )
    )
    assert isinstance(result, Failure)
    details = result.failure().details or {}
    assert details.get("abort") == "no_valid_seeds"
