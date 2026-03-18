from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rifthub_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from rifthub_backend.db.types import CATEGORY_ENUM, POST_STATUS_ENUM, POST_TYPE_ENUM
from rifthub_backend.db.types import Category, PostStatus, PostType

if TYPE_CHECKING:
    from .comment import Comment
    from .domain import Domain
    from .ingestion import IngestionItem
    from .source import Source
    from .user import User
    from .vote import PostVote


class Post(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint(
            "post_type != 'text' OR (body_markdown IS NOT NULL AND url IS NULL AND url_normalized IS NULL AND domain_id IS NULL)",
            name="text_fields",
        ),
        CheckConstraint(
            "post_type != 'link' OR (url IS NOT NULL AND url_normalized IS NOT NULL AND domain_id IS NOT NULL)",
            name="link_fields",
        ),
        CheckConstraint(
            "post_type != 'job' OR (url IS NOT NULL OR body_markdown IS NOT NULL)",
            name="job_fields",
        ),
        CheckConstraint(
            "(is_ingested = true AND ingested_from_source_id IS NOT NULL) "
            "OR "
            "(is_ingested = false AND ingested_from_source_id IS NULL)",
            name="ingestion_fields_coherent",
        ),
        CheckConstraint("upvote_count >= 0", name="upvote_count_nonnegative"),
        CheckConstraint("downvote_count >= 0", name="downvote_count_nonnegative"),
        CheckConstraint("comment_count >= 0", name="comment_count_nonnegative"),
        CheckConstraint("bookmark_count >= 0", name="bookmark_count_nonnegative"),
        CheckConstraint("view_count >= 0", name="view_count_nonnegative"),
        Index("ix_posts_author_id", "author_id"),
        Index("ix_posts_category", "category"),
        Index("ix_posts_post_type", "post_type"),
        Index("ix_posts_status", "status"),
        Index("ix_posts_submitted_at", "submitted_at"),
        Index("ix_posts_rank_score", "rank_score"),
        Index("ix_posts_status_rank_score", "status", "rank_score"),
        Index("ix_posts_category_status_submitted_at", "category", "status", "submitted_at"),
        Index("ix_posts_post_type_status_submitted_at", "post_type", "status", "submitted_at"),
        Index("ix_posts_domain_id", "domain_id"),
        Index("ix_posts_url_normalized", "url_normalized"),
        Index(
            "uq_posts_active_link_url_normalized",
            "url_normalized",
            unique=True,
            postgresql_where=text("post_type = 'link' AND status = 'active' AND url_normalized IS NOT NULL"),
        ),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_type: Mapped[PostType] = mapped_column(POST_TYPE_ENUM, nullable=False)
    category: Mapped[Category] = mapped_column(CATEGORY_ENUM, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    url_normalized: Mapped[str | None] = mapped_column(Text)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("domains.id"))
    body_markdown: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(
        POST_STATUS_ENUM,
        nullable=False,
        default=PostStatus.ACTIVE,
        server_default=text(f"'{PostStatus.ACTIVE.value}'"),
    )
    is_ingested: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    ingested_from_source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"))
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
    comment_count: Mapped[int] = mapped_column(
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
    bookmark_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_commented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    job_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author: Mapped["User"] = relationship(back_populates="posts")
    domain: Mapped["Domain | None"] = relationship(back_populates="posts")
    ingested_from_source: Mapped["Source | None"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")
    post_votes: Mapped[list["PostVote"]] = relationship(back_populates="post")
    linked_ingestion_items: Mapped[list["IngestionItem"]] = relationship(
        back_populates="linked_post",
        foreign_keys="IngestionItem.linked_post_id",
    )
    dedupe_ingestion_items: Mapped[list["IngestionItem"]] = relationship(
        back_populates="dedupe_match_post",
        foreign_keys="IngestionItem.dedupe_match_post_id",
    )
