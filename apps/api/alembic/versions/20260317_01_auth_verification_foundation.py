"""Phase 3 auth verification foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260317_01"
down_revision = "20260313_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    context = op.get_context()
    with context.autocommit_block():
        op.execute("ALTER TYPE user_status_enum ADD VALUE IF NOT EXISTS 'pending' BEFORE 'active'")

    op.alter_column(
        "users",
        "status",
        existing_type=sa.Enum(
            "pending",
            "active",
            "suspended",
            "banned",
            name="user_status_enum",
        ),
        server_default=sa.text("'pending'"),
        existing_nullable=False,
    )

    op.create_table(
        "user_verification_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_verification_tokens_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_user_verification_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_user_verification_tokens_token_hash"),
    )
    op.create_index(
        "ix_user_verification_tokens_user_id",
        "user_verification_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_user_verification_tokens_expires_at",
        "user_verification_tokens",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_verification_tokens_expires_at", table_name="user_verification_tokens")
    op.drop_index("ix_user_verification_tokens_user_id", table_name="user_verification_tokens")
    op.drop_table("user_verification_tokens")

    op.alter_column(
        "users",
        "status",
        existing_type=sa.Enum(
            "pending",
            "active",
            "suspended",
            "banned",
            name="user_status_enum",
        ),
        server_default=sa.text("'active'"),
        existing_nullable=False,
    )
