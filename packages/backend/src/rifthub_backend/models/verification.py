from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class UserVerificationToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_verification_tokens"
    __table_args__ = (
        Index("ix_user_verification_tokens_user_id", "user_id"),
        Index("ix_user_verification_tokens_expires_at", "expires_at"),
        Index(
            "uq_user_verification_tokens_active_user_id",
            "user_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    delivery_attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    last_delivery_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_provider_message_id: Mapped[str | None] = mapped_column(String(255))
    delivery_error: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="verification_tokens")
