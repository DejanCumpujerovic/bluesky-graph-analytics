"""Analysis run persistence port (DEO 7)."""

from typing import Any, Protocol

from returns.result import Result

from bluesky_graph_analytics.application.records import AnalysisRun, RunStatus
from bluesky_graph_analytics.domain.errors import DomainError
from bluesky_graph_analytics.domain.value_objects import SnapshotId


class RunRepository(Protocol):
    async def create(self, run: AnalysisRun) -> Result[AnalysisRun, DomainError]: ...

    async def get(self, run_id: int) -> Result[AnalysisRun | None, DomainError]: ...

    async def get_by_snapshot_id(
        self, snapshot_id: SnapshotId
    ) -> Result[AnalysisRun | None, DomainError]: ...

    async def update_stat(self, run_id: int, key: str, value: Any) -> Result[None, DomainError]: ...

    async def merge_stats_section(
        self, run_id: int, section: str, patch: dict[str, Any]
    ) -> Result[None, DomainError]: ...

    async def finalize_run(
        self, run_id: int, *, status: RunStatus = RunStatus.COMPLETED
    ) -> Result[None, DomainError]: ...

    async def force_resnapshot(self, snapshot_id: SnapshotId) -> Result[None, DomainError]: ...
