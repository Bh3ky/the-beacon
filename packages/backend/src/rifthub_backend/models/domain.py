from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .post import Post
    from .source import Source


class Domain(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "domains"
    __table_args__ = (
        CheckConstraint("trust_score > 0", name="trust_score_positive"),
        CheckConstraint("submission_count >= 0", name="submission_count_non_negative"),
        CheckConstraint("published_post_count >= 0", name="published_post_count_non_negative"),
        Index("ix_domains_is_blocked", "is_blocked"),
        Index("ix_domains_trust_score", "trust_score"),
    )

    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    trust_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default=text("1.00"),
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    submission_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    published_post_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    posts: Mapped[list["Post"]] = relationship(back_populates="domain")
    sources: Mapped[list["Source"]] = relationship(back_populates="domain")
