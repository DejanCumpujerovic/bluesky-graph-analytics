"""Deletion service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from returns.result import Failure, Success

from bluesky_graph_analytics.application.records import DeletionRecord
from bluesky_graph_analytics.application.services.deletion_service import DeletionService
from bluesky_graph_analytics.domain.value_objects import DID


@pytest.mark.asyncio
async def test_add_and_list_pending(session_factory, db_engine) -> None:
    deletions = MagicMock()
    deletions.record = AsyncMock(
        return_value=Success(
            DeletionRecord(
                subject_did="did:plc:x",
                requested_at=datetime.now(UTC),
                processed=False,
            )
        )
    )
    deletions.list_pending = AsyncMock(return_value=Success([]))

    svc = DeletionService(deletions, db_engine)
    result = await svc.add_request(did=DID("did:plc:x"))
    assert not isinstance(result, Failure)
    listed = await svc.list_pending()
    assert listed.unwrap() == []
