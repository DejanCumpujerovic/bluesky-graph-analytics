"""Bluesky API port."""

from typing import Protocol

from returns.result import Result

from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.models import FollowRelation, Profile
from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId


class BlueskyClient(Protocol):
    async def resolve_handle(self, handle: Handle) -> Result[DID, DomainError]: ...

    async def fetch_profile(self, did: DID) -> Result[Profile, DomainError]: ...

    async def fetch_followers(
        self, did: DID, *, snapshot_id: SnapshotId, limit: int
    ) -> Result[list[FollowRelation], DomainError]: ...

    async def fetch_following(
        self, did: DID, *, snapshot_id: SnapshotId, limit: int
    ) -> Result[list[FollowRelation], DomainError]: ...
