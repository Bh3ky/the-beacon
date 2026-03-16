from __future__ import annotations

import uuid

from sqlalchemy import Index, Text, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import (
    MODERATION_ACTION_TYPE_ENUM,
    MODERATION_TARGET_TYPE_ENUM,
    ModerationActionType,
    ModerationTargetType,
)

from .user import User


class ModerationAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_actions"
    __table_args__ = (
        Index("ix_moderation_actions_moderator_id", "moderator_id"),
        Index("ix_moderation_actions_target_type_target_id", "target_type", "target_id"),
        Index("ix_moderation_actions_action_type", "action_type"),
        Index("ix_moderation_actions_created_at", "created_at"),
    )

    moderator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type: Mapped[ModerationTargetType] = mapped_column(
        MODERATION_TARGET_TYPE_ENUM,
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    action_type: Mapped[ModerationActionType] = mapped_column(
        MODERATION_ACTION_TYPE_ENUM,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    moderator: Mapped[User] = relationship(back_populates="moderation_actions")
