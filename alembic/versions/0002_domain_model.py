"""Align persistence with DEO 4 domain model.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("description", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("followers_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "profiles",
        sa.Column("follows_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "profiles",
        sa.Column("posts_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "profiles",
        sa.Column("detected_language", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("language_confidence", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "profiles",
        sa.Column("is_seed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "profiles",
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_column("profiles", "collected_at")

    op.add_column("follows", sa.Column("snapshot_id", sa.String(length=64), nullable=True))
    op.execute("UPDATE follows SET snapshot_id = 'legacy' WHERE snapshot_id IS NULL")
    with op.batch_alter_table("follows") as batch_op:
        batch_op.alter_column("snapshot_id", nullable=False)
    op.drop_column("follows", "collected_at")


def downgrade() -> None:
    op.add_column(
        "follows",
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.drop_column("follows", "snapshot_id")

    op.add_column("profiles", sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("profiles", "ingested_at")
    op.drop_column("profiles", "is_seed")
    op.drop_column("profiles", "language_confidence")
    op.drop_column("profiles", "detected_language")
    op.drop_column("profiles", "posts_count")
    op.drop_column("profiles", "follows_count")
    op.drop_column("profiles", "followers_count")
    op.drop_column("profiles", "description")
