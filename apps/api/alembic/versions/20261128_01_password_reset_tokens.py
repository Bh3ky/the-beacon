"""Add password reset tokens.

Revision ID: 20261128_01
Revises: 20260324_04
Create Date: 2026-11-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261128_01"
down_revision: str | None = "20260324_04"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_password_reset_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_password_reset_tokens_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_password_reset_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_user_password_reset_tokens_token_hash"),
    )
    op.create_index(
        "ix_user_password_reset_tokens_user_id",
        "user_password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "uq_user_password_reset_tokens_active_user_id",
        "user_password_reset_tokens",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL"),
    )


def downgrade() -> None:
    # Dropping the table also drops its indexes.
    op.drop_table("user_password_reset_tokens")
