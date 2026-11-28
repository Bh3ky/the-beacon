from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class UserPasswordResetToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_password_reset_tokens"
    __table_args__ = (
        Index("ix_user_password_reset_tokens_user_id", "user_id"),
        Index(
            "uq_user_password_reset_tokens_active_user_id",
            "user_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")
