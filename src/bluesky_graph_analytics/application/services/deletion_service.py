"""Deletion / erasure use cases (DEO 5.8)."""

from datetime import UTC, datetime

import structlog
from returns.result import Failure, Result, Success
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from bluesky_graph_analytics.application.ports.bluesky_client import BlueskyClient
from bluesky_graph_analytics.application.ports.deletion_repository import DeletionRepository
from bluesky_graph_analytics.application.records import DeletionRecord
from bluesky_graph_analytics.domain.errors import DomainError, ErrorCode
from bluesky_graph_analytics.domain.value_objects import DID, Handle
from bluesky_graph_analytics.infrastructure.persistence.deletion_ops import (
    process_deletion_transaction,
)

logger = structlog.get_logger(__name__)


class DeletionService:
    def __init__(
        self,
        deletions: DeletionRepository,
        engine: AsyncEngine,
        bluesky: BlueskyClient | None = None,
    ) -> None:
        self._deletions = deletions
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)
        self._bluesky = bluesky

    async def add_request(
        self,
        *,
        did: DID | None = None,
        handle: Handle | None = None,
        reason: str | None = None,
    ) -> Result[DeletionRecord, DomainError]:
        subject = did
        if subject is None and handle is not None:
            if self._bluesky is None:
                return Failure(
                    DomainError(code=ErrorCode.VALIDATION, message="Cannot resolve handle")
                )
            resolved = await self._bluesky.resolve_handle(handle)
            if isinstance(resolved, Failure):
                return resolved
            subject = resolved.unwrap()
        if subject is None:
            return Failure(
                DomainError(code=ErrorCode.VALIDATION, message="Provide --did or --handle")
            )

        record = DeletionRecord(
            subject_did=str(subject),
            requested_at=datetime.now(UTC),
            reason=reason,
            processed=False,
        )
        stored = await self._deletions.record(record)
        if isinstance(stored, Failure):
            return stored
        return Success(record)

    async def list_pending(self) -> Result[list[DeletionRecord], DomainError]:
        return await self._deletions.list_pending()

    async def process_pending(self) -> Result[int, DomainError]:
        pending = await self._deletions.list_pending()
        if isinstance(pending, Failure):
            return pending
        count = 0
        for entry in pending.unwrap():
            try:
                await process_deletion_transaction(self._session_factory, DID(entry.subject_did))
            except Exception as exc:  # noqa: BLE001
                return Failure(DomainError(code=ErrorCode.PERSISTENCE, message=str(exc)))
            logger.info(
                "deletion_audit",
                did=entry.subject_did,
                reason=entry.reason,
                requested_at=entry.requested_at.isoformat(),
                action="erase_follows_and_profile",
            )
            count += 1
        return Success(count)
