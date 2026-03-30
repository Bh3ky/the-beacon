from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from rifthub_backend.db.types import (
    CommentStatus,
    FlagReason,
    FlagStatus,
    FlagTargetType,
    ModerationActionType,
    ModerationTargetType,
    PostStatus,
    PostType,
    UserRole,
    UserStatus,
)


class UserPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    bio: str | None
    role: UserRole
    status: UserStatus
    karma: int
    post_count: int
    comment_count: int
    avatar_url: str | None
    created_at: datetime
    last_active_at: datetime | None


class UserSummaryPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str


class DomainSummaryPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hostname: str
    display_name: str | None


class PageInfoPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    next_cursor: str | None
    has_next_page: bool


class PostPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    post_type: PostType
    category: str
    status: PostStatus
    url: str | None
    body_markdown: str | None
    author: UserSummaryPayload
    domain: DomainSummaryPayload | None
    upvote_count: int
    downvote_count: int
    comment_count: int
    score: int
    rank_score: float
    viewer_vote: int | None
    viewer_can_edit: bool
    viewer_can_moderate: bool
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    last_commented_at: datetime | None
    job_expires_at: datetime | None


class CommentPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    parent_comment_id: UUID | None
    depth: int
    body_markdown: str
    status: CommentStatus
    author: UserSummaryPayload
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: Literal[1, -1] | None
    viewer_can_edit: bool
    viewer_can_moderate: bool
    created_at: datetime
    updated_at: datetime


class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[PostPayload]
    page_info: PageInfoPayload


class PlatformSummaryPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    builders_this_month: int
    builders_delta_pct: float | None
    funding_stories_last_30d: int
    funding_stories_delta_pct: float | None
    posts_per_hour: float
    posts_per_hour_delta_pct: float | None
    comments_this_week: int
    comments_delta_pct: float | None
    jobs_live: int
    jobs_live_delta_pct: float | None


class FlagPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_type: FlagTargetType
    target_id: UUID
    reporter_id: UUID
    reason_code: FlagReason
    notes: str | None
    status: FlagStatus
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post: PostPayload


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment: CommentPayload


class CommentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[CommentPayload]
    page_info: PageInfoPayload


class PostVotePayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: Literal[1, -1] | None


class CommentVotePayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: Literal[1, -1] | None


class PostVoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post: PostVotePayload


class CommentVoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment: CommentVotePayload


class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    flag: FlagPayload


class ModerationTargetSummaryPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_type: FlagTargetType
    title: str | None
    excerpt: str | None
    username: str | None
    status: str


class FlagQueueItemPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    flag: FlagPayload
    reporter: UserSummaryPayload
    target: ModerationTargetSummaryPayload


class FlagQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[FlagQueueItemPayload]


class IngestionSourceSummaryPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    status: str
    auto_publish: bool


class IngestionReviewItemPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    url: str
    ingestion_status: str
    detected_category: str | None
    published_at_external: datetime | None
    discovered_at: datetime
    processing_notes: str | None
    source: IngestionSourceSummaryPayload
    linked_post_id: UUID | None
    dedupe_match_post_id: UUID | None


class IngestionReviewQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[IngestionReviewItemPayload]


class SourceHealthPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    status: str
    auto_publish: bool
    poll_interval_minutes: int
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None


class SourceHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[SourceHealthPayload]


class ModerationActionPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    moderator_id: UUID
    target_type: ModerationTargetType
    target_id: UUID
    action_type: ModerationActionType
    reason: str | None
    metadata_json: dict[str, object] | None
    created_at: datetime
    updated_at: datetime


class ModerationActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: ModerationActionPayload
    flag: FlagPayload | None
