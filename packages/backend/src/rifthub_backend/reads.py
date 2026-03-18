from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Literal
from uuid import UUID

from sqlalchemy import Select, and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.db.types import CommentStatus, PostStatus, PostType, UserRole
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.domain import Domain
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.models.vote import CommentVote, PostVote


CommentSort = Literal["top", "new", "old"]
FeedKind = Literal["top", "new", "jobs"]
COMMENT_READ_LIMIT = 500


@dataclass(slots=True)
class ReadError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


@dataclass(frozen=True, slots=True)
class UserSummary:
    id: UUID
    username: str


@dataclass(frozen=True, slots=True)
class DomainSummary:
    id: UUID
    hostname: str
    display_name: str | None


@dataclass(frozen=True, slots=True)
class PageInfo:
    next_cursor: str | None
    has_next_page: bool


@dataclass(frozen=True, slots=True)
class PostRead:
    id: UUID
    title: str
    slug: str
    post_type: PostType
    category: str
    status: PostStatus
    url: str | None
    body_markdown: str | None
    author: UserSummary
    domain: DomainSummary | None
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


@dataclass(frozen=True, slots=True)
class CommentRead:
    id: UUID
    post_id: UUID
    parent_comment_id: UUID | None
    depth: int
    body_markdown: str
    status: CommentStatus
    author: UserSummary
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: int | None
    viewer_can_edit: bool
    viewer_can_moderate: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class FeedPage:
    items: list[PostRead]
    page_info: PageInfo


@dataclass(frozen=True, slots=True)
class CommentPage:
    items: list[CommentRead]
    page_info: PageInfo


def _utcnow() -> datetime:
    return datetime.now(UTC)


def encode_feed_cursor(payload: dict[str, str | float]) -> str:
    # Stable key ordering keeps opaque cursors deterministic across identical payloads.
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_feed_cursor(cursor: str, *, kind: FeedKind) -> dict[str, str | float]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception as exc:
        raise ReadError(400, "validation_error", "Cursor is invalid.") from exc

    if not isinstance(payload, dict) or payload.get("kind") != kind:
        raise ReadError(400, "validation_error", "Cursor is invalid.")
    return payload


def _viewer_can_moderate(viewer_role: UserRole | None) -> bool:
    return viewer_role in {UserRole.MODERATOR, UserRole.ADMIN}


def _viewer_can_edit(*, viewer_user_id: UUID | None, author_id: UUID, status: PostStatus | CommentStatus) -> bool:
    return viewer_user_id == author_id and status in {PostStatus.ACTIVE, CommentStatus.ACTIVE}


def _domain_summary(domain: Domain | None) -> DomainSummary | None:
    if domain is None:
        return None
    return DomainSummary(
        id=domain.id,
        hostname=domain.hostname,
        display_name=domain.display_name,
    )


def _user_summary(user: User) -> UserSummary:
    return UserSummary(id=user.id, username=user.username)


def _serialize_post(
    *,
    post: Post,
    viewer_vote: int | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> PostRead:
    return PostRead(
        id=post.id,
        title=post.title,
        slug=post.slug,
        post_type=post.post_type,
        category=post.category.value,
        status=post.status,
        url=post.url,
        body_markdown=post.body_markdown,
        author=_user_summary(post.author),
        domain=_domain_summary(post.domain),
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        comment_count=post.comment_count,
        score=post.score,
        rank_score=post.rank_score,
        viewer_vote=viewer_vote,
        viewer_can_edit=_viewer_can_edit(
            viewer_user_id=viewer_user_id,
            author_id=post.author_id,
            status=post.status,
        ),
        viewer_can_moderate=_viewer_can_moderate(viewer_role),
        submitted_at=post.submitted_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        last_commented_at=post.last_commented_at,
        job_expires_at=post.job_expires_at,
    )


def _serialize_comment(
    *,
    comment: Comment,
    viewer_vote: int | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> CommentRead:
    return CommentRead(
        id=comment.id,
        post_id=comment.post_id,
        parent_comment_id=comment.parent_comment_id,
        depth=comment.depth,
        body_markdown=comment.body_markdown,
        status=comment.status,
        author=_user_summary(comment.author),
        upvote_count=comment.upvote_count,
        downvote_count=comment.downvote_count,
        score=comment.score,
        rank_score=comment.rank_score,
        viewer_vote=viewer_vote,
        viewer_can_edit=_viewer_can_edit(
            viewer_user_id=viewer_user_id,
            author_id=comment.author_id,
            status=comment.status,
        ),
        viewer_can_moderate=_viewer_can_moderate(viewer_role),
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def _base_post_query() -> Select[tuple[Post]]:
    return (
        select(Post)
        .options(joinedload(Post.author), joinedload(Post.domain))
        .where(Post.status == PostStatus.ACTIVE)
    )


def _apply_feed_cursor(
    *,
    query: Select[tuple[Post]],
    kind: FeedKind,
    cursor: str | None,
) -> Select[tuple[Post]]:
    if cursor is None:
        return query

    payload = decode_feed_cursor(cursor, kind=kind)
    try:
        cursor_id = UUID(str(payload["id"]))
        if kind == "top":
            rank_score = float(payload["rank_score"])
            return query.where(
                or_(
                    Post.rank_score < rank_score,
                    and_(Post.rank_score == rank_score, Post.id < cursor_id),
                )
            )

        submitted_at = datetime.fromisoformat(str(payload["submitted_at"]))
        return query.where(
            or_(
                Post.submitted_at < submitted_at,
                and_(Post.submitted_at == submitted_at, Post.id < cursor_id),
            )
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ReadError(400, "validation_error", "Cursor is invalid.") from exc


async def _viewer_post_votes(
    *,
    db: AsyncSession,
    viewer_user_id: UUID | None,
    post_ids: list[UUID],
) -> dict[UUID, int]:
    if viewer_user_id is None or not post_ids:
        return {}

    rows = await db.execute(
        select(PostVote.post_id, PostVote.vote_value).where(
            PostVote.user_id == viewer_user_id,
            PostVote.post_id.in_(post_ids),
        )
    )
    return {post_id: vote_value for post_id, vote_value in rows.all()}


async def _viewer_comment_votes(
    *,
    db: AsyncSession,
    viewer_user_id: UUID | None,
    comment_ids: list[UUID],
) -> dict[UUID, int]:
    if viewer_user_id is None or not comment_ids:
        return {}

    rows = await db.execute(
        select(CommentVote.comment_id, CommentVote.vote_value).where(
            CommentVote.user_id == viewer_user_id,
            CommentVote.comment_id.in_(comment_ids),
        )
    )
    return {comment_id: vote_value for comment_id, vote_value in rows.all()}


def _feed_page_info(*, kind: FeedKind, posts: list[Post], has_next_page: bool) -> PageInfo:
    if not has_next_page or not posts:
        return PageInfo(next_cursor=None, has_next_page=False)

    last_post = posts[-1]
    if kind == "top":
        cursor = encode_feed_cursor(
            {
                "kind": kind,
                "rank_score": last_post.rank_score,
                "id": str(last_post.id),
            }
        )
    else:
        cursor = encode_feed_cursor(
            {
                "kind": kind,
                "submitted_at": last_post.submitted_at.isoformat(),
                "id": str(last_post.id),
            }
        )
    return PageInfo(next_cursor=cursor, has_next_page=True)


async def _get_feed(
    *,
    db: AsyncSession,
    kind: FeedKind,
    limit: int,
    cursor: str | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> FeedPage:
    query = _base_post_query()
    if kind == "top":
        query = query.order_by(desc(Post.rank_score), desc(Post.id))
    elif kind == "new":
        query = query.order_by(desc(Post.submitted_at), desc(Post.id))
    else:
        # Jobs intentionally reuse submitted_at cursor ordering; expiry is only a visibility filter.
        now = _utcnow()
        query = query.where(
            Post.post_type == PostType.JOB,
            or_(Post.job_expires_at.is_(None), Post.job_expires_at > now),
        ).order_by(desc(Post.submitted_at), desc(Post.id))

    query = _apply_feed_cursor(query=query, kind=kind, cursor=cursor).limit(limit + 1)
    result = await db.execute(query)
    posts = result.scalars().unique().all()
    has_next_page = len(posts) > limit
    posts = posts[:limit]

    votes_by_post = await _viewer_post_votes(
        db=db,
        viewer_user_id=viewer_user_id,
        post_ids=[post.id for post in posts],
    )
    items = [
        _serialize_post(
            post=post,
            viewer_vote=votes_by_post.get(post.id),
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
        for post in posts
    ]
    return FeedPage(
        items=items,
        page_info=_feed_page_info(kind=kind, posts=posts, has_next_page=has_next_page),
    )


async def get_top_feed(
    *,
    db: AsyncSession,
    limit: int,
    cursor: str | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> FeedPage:
    return await _get_feed(
        db=db,
        kind="top",
        limit=limit,
        cursor=cursor,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
    )


async def get_new_feed(
    *,
    db: AsyncSession,
    limit: int,
    cursor: str | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> FeedPage:
    return await _get_feed(
        db=db,
        kind="new",
        limit=limit,
        cursor=cursor,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
    )


async def get_jobs_feed(
    *,
    db: AsyncSession,
    limit: int,
    cursor: str | None,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> FeedPage:
    return await _get_feed(
        db=db,
        kind="jobs",
        limit=limit,
        cursor=cursor,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
    )


async def get_post_detail(
    *,
    db: AsyncSession,
    post_id: UUID,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> PostRead:
    result = await db.execute(
        _base_post_query().where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise ReadError(404, "post_not_found", "The requested post does not exist.")

    viewer_vote = None
    if viewer_user_id is not None:
        viewer_vote = await db.scalar(
            select(PostVote.vote_value).where(
                PostVote.post_id == post.id,
                PostVote.user_id == viewer_user_id,
            )
        )

    return _serialize_post(
        post=post,
        viewer_vote=viewer_vote,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
    )


async def get_comment_detail(
    *,
    db: AsyncSession,
    comment_id: UUID,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> CommentRead:
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.author))
        .where(Comment.id == comment_id, Comment.status == CommentStatus.ACTIVE)
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise ReadError(404, "comment_not_found", "The requested comment does not exist.")

    viewer_vote = None
    if viewer_user_id is not None:
        viewer_vote = await db.scalar(
            select(CommentVote.vote_value).where(
                CommentVote.comment_id == comment.id,
                CommentVote.user_id == viewer_user_id,
            )
        )

    return _serialize_comment(
        comment=comment,
        viewer_vote=viewer_vote,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
    )


async def get_post_comments(
    *,
    db: AsyncSession,
    post_id: UUID,
    sort: CommentSort,
    viewer_user_id: UUID | None,
    viewer_role: UserRole | None,
) -> CommentPage:
    post_exists = await db.scalar(
        select(Post.id).where(Post.id == post_id, Post.status == PostStatus.ACTIVE)
    )
    if post_exists is None:
        raise ReadError(404, "post_not_found", "The requested post does not exist.")

    query = (
        select(Comment)
        .options(joinedload(Comment.author))
        .where(
            Comment.post_id == post_id,
            Comment.status == CommentStatus.ACTIVE,
        )
    )
    if sort == "top":
        query = query.order_by(desc(Comment.rank_score), desc(Comment.id))
    elif sort == "new":
        query = query.order_by(desc(Comment.created_at), desc(Comment.id))
    else:
        query = query.order_by(Comment.created_at, Comment.id)

    result = await db.execute(query.limit(COMMENT_READ_LIMIT))
    comments = result.scalars().unique().all()
    votes_by_comment = await _viewer_comment_votes(
        db=db,
        viewer_user_id=viewer_user_id,
        comment_ids=[comment.id for comment in comments],
    )
    items = [
        _serialize_comment(
            comment=comment,
            viewer_vote=votes_by_comment.get(comment.id),
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
        for comment in comments
    ]
    return CommentPage(
        items=items,
        page_info=PageInfo(next_cursor=None, has_next_page=False),
    )
