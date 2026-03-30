from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Final
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.db.types import Category, CommentStatus, PostStatus, PostType, UserRole
from rifthub_backend.domains import resolve_or_create_domain
from rifthub_backend.ingestion_normalization import (
    hostname_from_normalized_url,
    normalize_external_url,
)
from rifthub_backend.job_expiry import normalize_new_job_expiry
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.reads import CommentRead, PostRead, get_comment_detail, get_post_detail
from rifthub_backend.voting import compute_comment_rank_score, compute_post_rank_score
from rifthub_backend.write_access import user_has_restricted_write_access

MAX_COMMENT_DEPTH: Final = 6
MAX_SLUG_LENGTH: Final = 100
ACTIVE_LINK_URL_CONSTRAINT_NAME: Final = "uq_posts_active_link_url_normalized"


@dataclass(slots=True)
class CreationError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _require_active_author(*, user: User) -> None:
    if user_has_restricted_write_access(status=user.status):
        raise CreationError(403, "forbidden", "Your account cannot perform this action.")


def slugify_title(title: str) -> str:
    normalized = title.strip().lower()
    # v1 intentionally keeps slug generation ASCII-only; future iterations can add transliteration.
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if not normalized:
        normalized = "post"
    return normalized[:MAX_SLUG_LENGTH].rstrip("-") or "post"


def normalize_url(raw_url: str) -> str:
    try:
        return normalize_external_url(raw_url)
    except ValueError as exc:
        raise CreationError(422, "validation_error", str(exc)) from exc


def hostname_from_url(normalized_url: str) -> str:
    try:
        return hostname_from_normalized_url(normalized_url)
    except ValueError as exc:
        raise CreationError(422, "validation_error", str(exc)) from exc


def _duplicate_submission_error(*, existing_post: Post | None) -> CreationError:
    details: dict[str, str] | None = None
    if existing_post is not None:
        details = {
            "existing_post_id": str(existing_post.id),
            "existing_post_slug": existing_post.slug,
        }
    return CreationError(
        409,
        "duplicate_submission",
        "This story has already been submitted recently.",
        details=details,
    )


def _is_active_link_duplicate_error(exc: IntegrityError) -> bool:
    constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    return constraint_name == ACTIVE_LINK_URL_CONSTRAINT_NAME


@dataclass(frozen=True, slots=True)
class CreatePostInput:
    post_type: PostType
    category: Category
    title: str
    url: str | None
    body_markdown: str | None
    job_expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class CreateCommentInput:
    body_markdown: str
    parent_comment_id: UUID | None


async def create_post(
    *,
    db: AsyncSession,
    author: User,
    payload: CreatePostInput,
) -> PostRead:
    _require_active_author(user=author)

    title = payload.title.strip()
    body_markdown = payload.body_markdown.strip() if payload.body_markdown is not None else None
    if not title:
        raise CreationError(422, "validation_error", "Title is required.")
    if payload.post_type == PostType.TEXT and not body_markdown:
        raise CreationError(422, "validation_error", "Text posts require body_markdown.")
    if payload.post_type == PostType.LINK and not payload.url:
        raise CreationError(422, "validation_error", "Link posts require url.")
    if payload.post_type == PostType.JOB and not (payload.url or body_markdown):
        raise CreationError(422, "validation_error", "Job posts require url or body_markdown.")

    slug = slugify_title(title)
    normalized_url: str | None = None
    raw_url: str | None = None
    domain: Domain | None = None

    if payload.post_type in {PostType.LINK, PostType.JOB} and payload.url:
        raw_url = payload.url.strip()
        normalized_url = normalize_url(raw_url)
        hostname = hostname_from_url(normalized_url)
        domain = await resolve_or_create_domain(db=db, hostname=hostname)

    if payload.post_type == PostType.LINK and normalized_url is not None:
        existing_post = await db.scalar(
            select(Post).where(
                Post.status == PostStatus.ACTIVE,
                Post.url_normalized == normalized_url,
            )
        )
        if existing_post is not None:
            raise _duplicate_submission_error(existing_post=existing_post)

    now = _utcnow()
    try:
        resolved_job_expires_at = normalize_new_job_expiry(
            post_type=payload.post_type,
            requested_job_expires_at=payload.job_expires_at,
            now=now,
        )
    except ValueError as exc:
        raise CreationError(422, "validation_error", str(exc)) from exc
    initial_rank_score = compute_post_rank_score(
        score=0,
        submitted_at=now,
        comment_count=0,
        category=payload.category,
        domain_trust_score=domain.trust_score if domain is not None else None,
        now=now,
    )
    post = Post(
        author_id=author.id,
        post_type=payload.post_type,
        category=payload.category,
        title=title,
        slug=slug,
        url=raw_url if payload.post_type in {PostType.LINK, PostType.JOB} else None,
        url_normalized=normalized_url if payload.post_type in {PostType.LINK, PostType.JOB} else None,
        domain_id=domain.id if domain is not None else None,
        body_markdown=body_markdown,
        status=PostStatus.ACTIVE,
        is_ingested=False,
        rank_score=initial_rank_score,
        submitted_at=now,
        job_expires_at=resolved_job_expires_at,
    )
    db.add(post)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if payload.post_type == PostType.LINK and normalized_url is not None and _is_active_link_duplicate_error(exc):
            existing_post = await db.scalar(
                select(Post).where(
                    Post.status == PostStatus.ACTIVE,
                    Post.url_normalized == normalized_url,
                )
            )
            raise _duplicate_submission_error(existing_post=existing_post) from exc
        raise
    return await get_post_detail(
        db=db,
        post_id=post.id,
        viewer_user_id=author.id,
        viewer_role=author.role,
    )


async def create_comment(
    *,
    db: AsyncSession,
    author: User,
    post_id: UUID,
    payload: CreateCommentInput,
) -> CommentRead:
    _require_active_author(user=author)

    body_markdown = payload.body_markdown.strip()
    if not body_markdown:
        raise CreationError(422, "validation_error", "Comment body is required.")

    post = await db.scalar(
        select(Post)
        .options(joinedload(Post.domain))
        .where(Post.id == post_id, Post.status == PostStatus.ACTIVE)
    )
    if post is None:
        raise CreationError(404, "post_not_found", "The requested post does not exist.")

    depth = 0
    if payload.parent_comment_id is not None:
        parent = await db.scalar(
            select(Comment).where(
                Comment.id == payload.parent_comment_id,
                Comment.post_id == post_id,
                Comment.status == CommentStatus.ACTIVE,
            )
        )
        if parent is None:
            raise CreationError(404, "comment_not_found", "The requested comment does not exist.")
        depth = parent.depth + 1
        # MAX_COMMENT_DEPTH = 6 means root depth 0 plus replies up to depth 6.
        if depth > MAX_COMMENT_DEPTH:
            raise CreationError(422, "validation_error", "Comment depth exceeds the allowed maximum.")

    now = _utcnow()
    comment = Comment(
        post_id=post_id,
        author_id=author.id,
        parent_comment_id=payload.parent_comment_id,
        body_markdown=body_markdown,
        status=CommentStatus.ACTIVE,
        depth=depth,
        created_at=now,
        rank_score=compute_comment_rank_score(score=0, created_at=now, now=now),
    )
    db.add(comment)
    await db.flush()
    next_comment_count = post.comment_count + 1
    next_post_rank_score = compute_post_rank_score(
        score=post.score,
        submitted_at=post.submitted_at,
        comment_count=next_comment_count,
        category=post.category,
        domain_trust_score=post.domain.trust_score if post.domain is not None else None,
        now=now,
    )
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(
            comment_count=Post.comment_count + 1,
            last_commented_at=now,
            rank_score=next_post_rank_score,
        )
    )
    await db.commit()
    return await get_comment_detail(
        db=db,
        comment_id=comment.id,
        viewer_user_id=author.id,
        viewer_role=author.role,
    )
