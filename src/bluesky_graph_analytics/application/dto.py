"""Data transfer objects for application layer boundaries."""

from pydantic import BaseModel, Field

from bluesky_graph_analytics.domain.value_objects import Handle, SnapshotId


class CollectRequestDTO(BaseModel):
    seed_handles: list[Handle] = Field(default_factory=list)
    topic: str | None = None
    snapshot_id: SnapshotId | None = None
    run_label: str = Field(default="collection")
    force_resnapshot: bool = False


class AnalysisRequestDTO(BaseModel):
    run_label: str = "default"
    snapshot_id: SnapshotId | None = None


class ExportRequestDTO(BaseModel):
    snapshot_id: SnapshotId | None = None
    anonymized: bool = True
    output: str | None = None
    run_label: str = "default"  # legacy; results keyed by snapshot_id
