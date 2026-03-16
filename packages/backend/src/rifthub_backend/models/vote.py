from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .comment import Comment
    from .post import Post
    from .user import User


class PostVote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "post_votes"
    __table_args__ = (
        CheckConstraint("vote_value IN (-1, 1)", name="vote_value_allowed"),
        Index("uq_post_votes_post_id_user_id", "post_id", "user_id", unique=True),
        Index("ix_post_votes_user_id", "user_id"),
        Index("ix_post_votes_post_id", "post_id"),
    )

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    vote_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    post: Mapped["Post"] = relationship(back_populates="post_votes")
    user: Mapped["User"] = relationship(back_populates="post_votes")


class CommentVote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "comment_votes"
    __table_args__ = (
        CheckConstraint("vote_value IN (-1, 1)", name="vote_value_allowed"),
        Index("uq_comment_votes_comment_id_user_id", "comment_id", "user_id", unique=True),
        Index("ix_comment_votes_user_id", "user_id"),
        Index("ix_comment_votes_comment_id", "comment_id"),
    )

    comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comments.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    vote_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    comment: Mapped["Comment"] = relationship(back_populates="comment_votes")
    user: Mapped["User"] = relationship(back_populates="comment_votes")
