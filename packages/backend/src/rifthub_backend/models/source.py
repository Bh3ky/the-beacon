from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import CATEGORY_ENUM, SOURCE_STATUS_ENUM, SOURCE_TYPE_ENUM
from rifthub_backend.db.types import Category, SourceStatus, SourceType

if TYPE_CHECKING:
    from .domain import Domain
    from .ingestion import IngestionItem
    from .post import Post


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint("poll_interval_minutes > 0", name="poll_interval_positive"),
        CheckConstraint("trust_score > 0", name="trust_score_positive"),
        Index("ix_sources_status", "status"),
        Index("ix_sources_auto_publish", "auto_publish"),
        Index("ix_sources_last_checked_at", "last_checked_at"),
        Index("ix_sources_domain_id", "domain_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SOURCE_TYPE_ENUM, nullable=False)
    status: Mapped[SourceStatus] = mapped_column(
        SOURCE_STATUS_ENUM,
        nullable=False,
        default=SourceStatus.ACTIVE,
        server_default=SourceStatus.ACTIVE.value,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    site_url: Mapped[str | None] = mapped_column(Text)
    default_category: Mapped[Category | None] = mapped_column(CATEGORY_ENUM)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("domains.id"))
    trust_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default=text("1.00"),
    )
    auto_publish: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    poll_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default=text("30"),
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[str | None] = mapped_column(Text)

    domain: Mapped["Domain | None"] = relationship(back_populates="sources")
    posts: Mapped[list["Post"]] = relationship(back_populates="ingested_from_source")
    ingestion_items: Mapped[list["IngestionItem"]] = relationship(back_populates="source")
