"""Add conditional polling cache headers to sources.

Revision ID: 20260324_02
Revises: 20260324_01
Create Date: 2026-03-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_02"
down_revision: str | None = "20260324_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("last_etag", sa.String(length=255), nullable=True))
    op.add_column("sources", sa.Column("last_modified_header", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("sources", "last_modified_header")
    op.drop_column("sources", "last_etag")
