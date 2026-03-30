"""Add URL fallback uniqueness for ingestion items without external IDs.

Revision ID: 20260324_03
Revises: 20260324_02
Create Date: 2026-03-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_03"
down_revision: str | None = "20260324_02"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_ingestion_items_source_id_url_normalized_no_external_id",
        "ingestion_items",
        ["source_id", "url_normalized"],
        unique=True,
        postgresql_where=sa.text("external_id IS NULL AND url_normalized IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_ingestion_items_source_id_url_normalized_no_external_id",
        table_name="ingestion_items",
    )
