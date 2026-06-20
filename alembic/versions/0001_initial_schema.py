"""Initial schema — profiles, follows, runs, deletions.

Revision ID: 0001
Revises:
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("did", sa.String(length=256), primary_key=True),
        sa.Column("handle", sa.String(length=256), nullable=True),
        sa.Column("display_name", sa.String(length=512), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "follows",
        sa.Column("follower_did", sa.String(length=256), primary_key=True),
        sa.Column("followee_did", sa.String(length=256), primary_key=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "deletion_requests",
        sa.Column("subject_did", sa.String(length=256), primary_key=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("deletion_requests")
    op.drop_table("analysis_runs")
    op.drop_table("follows")
    op.drop_table("profiles")
