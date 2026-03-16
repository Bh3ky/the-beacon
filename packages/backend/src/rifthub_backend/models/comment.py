from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import COMMENT_STATUS_ENUM, CommentStatus

if TYPE_CHECKING:
    from .post import Post
    from .user import User
    from .vote import CommentVote


class Comment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("depth >= 0", name="depth_nonnegative"),
        CheckConstraint("upvote_count >= 0", name="upvote_count_nonnegative"),
        CheckConstraint("downvote_count >= 0", name="downvote_count_nonnegative"),
        CheckConstraint(
            "parent_comment_id IS NULL OR parent_comment_id <> id",
            name="parent_comment_not_self",
        ),
        UniqueConstraint("id", "post_id"),
        ForeignKeyConstraint(
            ["parent_comment_id", "post_id"],
            ["comments.id", "comments.post_id"],
        ),
        Index("ix_comments_post_id", "post_id"),
        Index("ix_comments_author_id", "author_id"),
        Index("ix_comments_parent_comment_id", "parent_comment_id"),
        Index("ix_comments_post_id_created_at", "post_id", "created_at"),
        Index("ix_comments_post_id_rank_score", "post_id", "rank_score"),
        Index("ix_comments_post_id_parent_comment_id", "post_id", "parent_comment_id"),
    )

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("comments.id"))
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommentStatus] = mapped_column(
        COMMENT_STATUS_ENUM,
        nullable=False,
        default=CommentStatus.ACTIVE,
        server_default=text(f"'{CommentStatus.ACTIVE.value}'"),
    )
    depth: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    upvote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    downvote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    rank_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default=text("0"),
    )

    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")
    parent_comment: Mapped["Comment | None"] = relationship(
        remote_side="Comment.id",
        back_populates="replies",
    )
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent_comment")
    comment_votes: Mapped[list["CommentVote"]] = relationship(back_populates="comment")
