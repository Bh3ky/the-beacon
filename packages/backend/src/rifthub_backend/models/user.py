from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import USER_ROLE_ENUM, USER_STATUS_ENUM, UserRole, UserStatus

if TYPE_CHECKING:
    from .comment import Comment
    from .flag import Flag
    from .moderation import ModerationAction
    from .post import Post
    from .session import UserSession
    from .vote import CommentVote, PostVote


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("char_length(username) BETWEEN 3 AND 32", name="username_length"),
        CheckConstraint("username ~ '^[a-z0-9_]+$'", name="username_format"),
        CheckConstraint("post_count >= 0", name="post_count_non_negative"),
        CheckConstraint("comment_count >= 0", name="comment_count_non_negative"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        Index("ix_users_created_at", "created_at"),
    )

    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        USER_ROLE_ENUM,
        nullable=False,
        default=UserRole.USER,
        server_default=text(f"'{UserRole.USER.value}'"),
    )
    status: Mapped[UserStatus] = mapped_column(
        USER_STATUS_ENUM,
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=text(f"'{UserStatus.ACTIVE.value}'"),
    )
    karma: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    post_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    post_votes: Mapped[list["PostVote"]] = relationship(back_populates="user")
    comment_votes: Mapped[list["CommentVote"]] = relationship(back_populates="user")
    reported_flags: Mapped[list["Flag"]] = relationship(
        back_populates="reporter",
        foreign_keys="Flag.reporter_id",
    )
    reviewed_flags: Mapped[list["Flag"]] = relationship(
        back_populates="reviewed_by_user",
        foreign_keys="Flag.reviewed_by_user_id",
    )
    moderation_actions: Mapped[list["ModerationAction"]] = relationship(
        back_populates="moderator",
    )
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
