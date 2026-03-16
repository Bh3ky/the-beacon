from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import CATEGORY_ENUM, INGESTION_STATUS_ENUM, Category, IngestionStatus

if TYPE_CHECKING:
    from .post import Post
    from .source import Source


class IngestionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_items"
    __table_args__ = (
        Index("ix_ingestion_items_source_id", "source_id"),
        Index("ix_ingestion_items_ingestion_status", "ingestion_status"),
        Index("ix_ingestion_items_published_at_external", "published_at_external"),
        Index("ix_ingestion_items_url_normalized", "url_normalized"),
        Index("ix_ingestion_items_linked_post_id", "linked_post_id"),
        Index(
            "uq_ingestion_items_source_id_external_id",
            "source_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_normalized: Mapped[str | None] = mapped_column(Text)
    published_at_external: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ingestion_status: Mapped[IngestionStatus] = mapped_column(
        INGESTION_STATUS_ENUM,
        nullable=False,
        default=IngestionStatus.DISCOVERED,
        server_default=text(f"'{IngestionStatus.DISCOVERED.value}'"),
    )
    detected_category: Mapped[Category | None] = mapped_column(CATEGORY_ENUM)
    linked_post_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("posts.id"))
    dedupe_match_post_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("posts.id"))
    raw_payload_json: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    processing_notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped["Source"] = relationship(back_populates="ingestion_items")
    linked_post: Mapped["Post | None"] = relationship(
        back_populates="linked_ingestion_items",
        foreign_keys=[linked_post_id],
    )
    dedupe_match_post: Mapped["Post | None"] = relationship(
        back_populates="dedupe_ingestion_items",
        foreign_keys=[dedupe_match_post_id],
    )
