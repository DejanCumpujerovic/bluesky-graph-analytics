"""Domain entities (no created_at / updated_at — infrastructure concern)."""

from pydantic import BaseModel, ConfigDict, Field

from bluesky_graph_analytics.domain.value_objects import DID, Handle, SnapshotId


class Profile(BaseModel):
    model_config = ConfigDict(frozen=True)

    did: DID
    handle: Handle | None = None
    display_name: str | None = None
    description: str | None = None
    followers_count: int = Field(default=0, ge=0)
    follows_count: int = Field(default=0, ge=0)
    posts_count: int = Field(default=0, ge=0)
    detected_language: str | None = None
    language_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_seed: bool = False


class FollowRelation(BaseModel):
    model_config = ConfigDict(frozen=True)

    follower_did: DID
    followee_did: DID
    snapshot_id: SnapshotId


class Community(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    member_dids: frozenset[DID]
    modularity_contribution: float
    top_terms: tuple[str, ...] = Field(default_factory=tuple)


class LinkPrediction(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_did: DID
    target_did: DID
    score: float = Field(ge=0.0, le=1.0)
    method: str
