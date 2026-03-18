"""Enforce one active verification token per user.

Revision ID: 20260318_02
Revises: 20260318_01
Create Date: 2026-03-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260318_02"
down_revision: str | None = "20260318_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_user_verification_tokens_active_user_id",
        "user_verification_tokens",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_user_verification_tokens_active_user_id", table_name="user_verification_tokens")
