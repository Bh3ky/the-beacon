"""Add ingestion_item as a moderation target type.

Revision ID: 20260324_04
Revises: 20260324_03
Create Date: 2026-03-24
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260324_04"
down_revision: str | None = "20260324_03"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE moderation_target_type_enum ADD VALUE IF NOT EXISTS 'ingestion_item'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
