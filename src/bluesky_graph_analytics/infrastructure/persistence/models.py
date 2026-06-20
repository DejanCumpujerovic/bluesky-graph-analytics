"""SQLAlchemy ORM models (DEO 7 — Phase 1 schema)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    git_commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    label: Mapped[str] = mapped_column(String(128), nullable=False, default="default")


class ProfileRow(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        Index("ix_profile_did", "did"),
        Index("ix_profile_handle", "handle"),
        Index("ix_profile_run", "run_id"),
    )

    did: Mapped[str] = mapped_column(String(256), primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    handle: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    followers_count: Mapped[int] = mapped_column(Integer, default=0)
    follows_count: Mapped[int] = mapped_column(Integer, default=0)
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    detected_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    language_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FollowRow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        Index("ix_follow_follower", "follower_did", "snapshot_id"),
        Index("ix_follow_followee", "followee_did", "snapshot_id"),
        Index("ix_follow_snapshot", "snapshot_id"),
    )

    follower_did: Mapped[str] = mapped_column(String(256), primary_key=True)
    followee_did: Mapped[str] = mapped_column(String(256), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeletionRow(Base):
    __tablename__ = "deletion_requests"

    did: Mapped[str] = mapped_column(String(256), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)


# Legacy alias for imports during transition
AnalysisRunRow = RunRow
