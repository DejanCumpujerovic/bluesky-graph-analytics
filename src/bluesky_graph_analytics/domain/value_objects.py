"""Domain value objects (NewType aliases and frozen Pydantic models)."""

from typing import Literal, NewType

from pydantic import BaseModel, ConfigDict, Field

DID = NewType("DID", str)
Handle = NewType("Handle", str)
SnapshotId = NewType("SnapshotId", str)
PseudonymHash = NewType("PseudonymHash", str)

SimilarityMetricName = Literal["jaccard", "adamic_adar", "overlap"]


class SimilarityScore(BaseModel):
    """Normalized similarity between two nodes in a graph snapshot."""

    model_config = ConfigDict(frozen=True)

    metric_name: SimilarityMetricName
    value: float = Field(ge=0.0, le=1.0)
    overlap_size: int = Field(ge=0)
