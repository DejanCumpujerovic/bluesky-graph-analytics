"""Methodology fields on runs and deletion requests.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analysis_runs", sa.Column("snapshot_id", sa.String(length=64), nullable=True))
    op.add_column("analysis_runs", sa.Column("config_snapshot", sa.Text(), nullable=True))
    op.add_column(
        "analysis_runs",
        sa.Column("git_commit_hash", sa.String(length=64), nullable=True),
    )
    op.add_column("analysis_runs", sa.Column("stats", sa.JSON(), nullable=True))
    op.execute("UPDATE analysis_runs SET snapshot_id = 'legacy' WHERE snapshot_id IS NULL")
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.alter_column("snapshot_id", nullable=False)

    op.add_column("deletion_requests", sa.Column("reason", sa.String(length=512), nullable=True))
    op.add_column(
        "deletion_requests",
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "deletion_requests",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Migrate legacy completed_at → processed_at
    op.execute(
        "UPDATE deletion_requests SET processed = 1, processed_at = completed_at "
        "WHERE completed_at IS NOT NULL"
    )
    op.drop_column("deletion_requests", "completed_at")


def downgrade() -> None:
    op.add_column(
        "deletion_requests",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE deletion_requests SET completed_at = processed_at WHERE processed = 1")
    op.drop_column("deletion_requests", "processed_at")
    op.drop_column("deletion_requests", "processed")
    op.drop_column("deletion_requests", "reason")

    op.drop_column("analysis_runs", "stats")
    op.drop_column("analysis_runs", "git_commit_hash")
    op.drop_column("analysis_runs", "config_snapshot")
    op.drop_column("analysis_runs", "snapshot_id")
