"""GDPR / deletion request persistence port."""

from typing import Protocol

from returns.result import Result

from bluesky_graph_analytics.application.records import DeletionRecord
from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.value_objects import DID


class DeletionRepository(Protocol):
    async def record(self, entry: DeletionRecord) -> Result[None, DomainError]: ...

    async def list_pending(self) -> Result[list[DeletionRecord], DomainError]: ...

    async def is_deleted(self, did: DID) -> Result[bool, DomainError]: ...

    async def load_deleted_set(self) -> Result[frozenset[DID], DomainError]: ...

    async def mark_processed(self, did: DID) -> Result[None, DomainError]: ...
