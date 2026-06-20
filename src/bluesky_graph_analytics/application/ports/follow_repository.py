"""Follow relation persistence port."""

from typing import Protocol

from returns.result import Result

from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.models import FollowRelation
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId


class FollowRepository(Protocol):
    async def save_relations(self, relations: list[FollowRelation]) -> Result[int, DomainError]: ...

    async def list_by_snapshot(
        self, snapshot_id: SnapshotId
    ) -> Result[list[FollowRelation], DomainError]: ...

    async def list_for_seed(self, seed_did: DID) -> Result[list[FollowRelation], DomainError]: ...

    async def delete_involving(self, did: DID) -> Result[int, DomainError]: ...

    async def delete_by_snapshot(self, snapshot_id: SnapshotId) -> Result[int, DomainError]: ...
