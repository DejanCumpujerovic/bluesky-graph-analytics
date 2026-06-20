"""DEO 7 — runs (int PK), profiles (did, run_id), follows indexes, deletion did PK.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-24

Destructive for MVP dev DBs: drops legacy tables and recreates DEO 7 schema.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("follows")
    op.drop_table("profiles")
    op.drop_table("analysis_runs")
    op.drop_table("deletion_requests")

    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_snapshot", sa.Text(), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
        sa.Column("git_commit_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("label", sa.String(length=128), nullable=False, server_default="default"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id"),
    )

    op.create_table(
        "profiles",
        sa.Column("did", sa.String(length=256), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("handle", sa.String(length=256), nullable=True),
        sa.Column("display_name", sa.String(length=512), nullable=True),
        sa.Column("description", sa.String(length=2048), nullable=True),
        sa.Column("followers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("follows_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detected_language", sa.String(length=16), nullable=True),
        sa.Column("language_confidence", sa.Float(), nullable=True),
        sa.Column("is_seed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("did", "run_id"),
    )
    op.create_index("ix_profile_did", "profiles", ["did"])
    op.create_index("ix_profile_handle", "profiles", ["handle"])
    op.create_index("ix_profile_run", "profiles", ["run_id"])

    op.create_table(
        "follows",
        sa.Column("follower_did", sa.String(length=256), nullable=False),
        sa.Column("followee_did", sa.String(length=256), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("follower_did", "followee_did", "snapshot_id"),
    )
    op.create_index("ix_follow_follower", "follows", ["follower_did", "snapshot_id"])
    op.create_index("ix_follow_followee", "follows", ["followee_did", "snapshot_id"])
    op.create_index("ix_follow_snapshot", "follows", ["snapshot_id"])

    op.create_table(
        "deletion_requests",
        sa.Column("did", sa.String(length=256), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("did"),
    )


def downgrade() -> None:
    op.drop_table("deletion_requests")
    op.drop_table("follows")
    op.drop_table("profiles")
    op.drop_table("runs")

    op.create_table(
        "profiles",
        sa.Column("did", sa.String(length=256), primary_key=True),
        sa.Column("handle", sa.String(length=256), nullable=True),
        sa.Column("display_name", sa.String(length=512), nullable=True),
        sa.Column("description", sa.String(length=2048), nullable=True),
        sa.Column("followers_count", sa.Integer(), server_default="0"),
        sa.Column("follows_count", sa.Integer(), server_default="0"),
        sa.Column("posts_count", sa.Integer(), server_default="0"),
        sa.Column("detected_language", sa.String(length=16), nullable=True),
        sa.Column("language_confidence", sa.Float(), server_default="0"),
        sa.Column("is_seed", sa.Boolean(), server_default=sa.false()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "follows",
        sa.Column("follower_did", sa.String(length=256), primary_key=True),
        sa.Column("followee_did", sa.String(length=256), primary_key=True),
        sa.Column("snapshot_id", sa.String(length=64), primary_key=True),
    )
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_snapshot", sa.Text(), nullable=True),
        sa.Column("git_commit_hash", sa.String(length=64), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
    )
    op.create_table(
        "deletion_requests",
        sa.Column("subject_did", sa.String(length=256), primary_key=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("processed", sa.Boolean(), server_default=sa.false()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
