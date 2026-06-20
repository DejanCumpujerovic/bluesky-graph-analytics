"""Profile persistence port (DEO 7)."""

from typing import Protocol

from returns.result import Result

from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.models import Profile
from bluesky_graph_analytics.domain.value_objects import DID, SnapshotId


class ProfileRepository(Protocol):
    async def upsert(self, profile: Profile, *, run_id: int) -> Result[None, DomainError]: ...

    async def get(self, did: DID, *, run_id: int) -> Result[Profile | None, DomainError]: ...

    async def delete(self, did: DID) -> Result[None, DomainError]: ...

    async def list_seeds(self, snapshot_id: SnapshotId) -> Result[list[Profile], DomainError]: ...

    async def list_for_snapshot(
        self, snapshot_id: SnapshotId
    ) -> Result[list[Profile], DomainError]: ...
