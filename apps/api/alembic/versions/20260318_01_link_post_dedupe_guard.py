"""Add DB-backed dedupe guard for active link post URLs.

Revision ID: 20260318_01
Revises: 20260317_01
Create Date: 2026-03-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260318_01"
down_revision: str | None = "20260317_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_posts_active_link_url_normalized",
        "posts",
        ["url_normalized"],
        unique=True,
        postgresql_where=sa.text("post_type = 'link' AND status = 'active' AND url_normalized IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_posts_active_link_url_normalized", table_name="posts")
