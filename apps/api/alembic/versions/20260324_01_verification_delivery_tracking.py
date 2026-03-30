"""Track verification delivery outcomes on active tokens.

Revision ID: 20260324_01
Revises: 20260318_02
Create Date: 2026-03-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_01"
down_revision: str | None = "20260318_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_verification_tokens",
        sa.Column(
            "delivery_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column(
            "delivery_attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column("last_delivery_attempted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column("delivery_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column("delivery_failed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column("delivery_provider_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "user_verification_tokens",
        sa.Column("delivery_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_verification_tokens", "delivery_error")
    op.drop_column("user_verification_tokens", "delivery_provider_message_id")
    op.drop_column("user_verification_tokens", "delivery_failed_at")
    op.drop_column("user_verification_tokens", "delivery_sent_at")
    op.drop_column("user_verification_tokens", "last_delivery_attempted_at")
    op.drop_column("user_verification_tokens", "delivery_attempt_count")
    op.drop_column("user_verification_tokens", "delivery_status")
