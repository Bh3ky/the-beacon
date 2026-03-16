from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import (
    FLAG_REASON_ENUM,
    FLAG_STATUS_ENUM,
    FLAG_TARGET_TYPE_ENUM,
    FlagReason,
    FlagStatus,
    FlagTargetType,
)

if TYPE_CHECKING:
    from .user import User


class Flag(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "flags"
    __table_args__ = (
        CheckConstraint(
            "(status = 'open' AND reviewed_by_user_id IS NULL AND reviewed_at IS NULL) "
            "OR "
            "(status <> 'open' AND reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="review_state_coherent",
        ),
        Index("ix_flags_target_type_target_id", "target_type", "target_id"),
        Index("ix_flags_reporter_id", "reporter_id"),
        Index("ix_flags_status", "status"),
        Index("ix_flags_created_at", "created_at"),
        Index(
            "uq_flags_open_reporter_target_reason",
            "reporter_id",
            "target_type",
            "target_id",
            "reason_code",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    target_type: Mapped[FlagTargetType] = mapped_column(FLAG_TARGET_TYPE_ENUM, nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason_code: Mapped[FlagReason] = mapped_column(FLAG_REASON_ENUM, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FlagStatus] = mapped_column(
        FLAG_STATUS_ENUM,
        nullable=False,
        default=FlagStatus.OPEN,
        server_default=text(f"'{FlagStatus.OPEN.value}'"),
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reporter: Mapped["User"] = relationship(
        back_populates="reported_flags",
        foreign_keys=[reporter_id],
    )
    reviewed_by_user: Mapped["User | None"] = relationship(
        back_populates="reviewed_flags",
        foreign_keys=[reviewed_by_user_id],
    )
