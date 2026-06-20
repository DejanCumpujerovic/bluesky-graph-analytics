"""Application / persistence records (operational, not graph domain entities)."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bluesky_graph_analytics.domain.value_objects import SnapshotId


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    FORCE_RESNAPSHOT = "force_resnapshot"


class AnalysisRun(BaseModel):
    model_config = ConfigDict(frozen=False)

    id: int | None = None
    started_at: datetime
    finished_at: datetime | None = None
    label: str = Field(default="default")
    snapshot_id: SnapshotId = SnapshotId("snap_default")
    config_snapshot: str | None = None
    git_commit_hash: str | None = None
    stats: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus = RunStatus.RUNNING


class DeletionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject_did: str  # DID value as str for ORM `did` column
    requested_at: datetime
    reason: str | None = None
    processed: bool = False
    processed_at: datetime | None = None
