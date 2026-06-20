"""Transactional deletion processing (DEO 5.8)."""

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bluesky_graph_analytics.domain.value_objects import DID
from bluesky_graph_analytics.infrastructure.persistence.models import (
    DeletionRow,
    FollowRow,
    ProfileRow,
)


async def process_deletion_transaction(
    session_factory: async_sessionmaker[AsyncSession],
    did: DID,
) -> None:
    async with session_factory() as session, session.begin():
        await session.execute(
            delete(FollowRow).where(
                (FollowRow.follower_did == did) | (FollowRow.followee_did == did)
            )
        )
        await session.execute(delete(ProfileRow).where(ProfileRow.did == did))
        row = await session.get(DeletionRow, str(did))
        if row is not None:
            row.processed = True
            row.processed_at = datetime.now(UTC)
