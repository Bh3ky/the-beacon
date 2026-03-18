from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Final
from urllib.parse import SplitResult, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import Category, CommentStatus, PostStatus, PostType, UserRole
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.domain import Domain
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.reads import CommentRead, PostRead, get_comment_detail, get_post_detail
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


def _normalized_split(raw_url: str) -> SplitResult:
    candidate = raw_url.strip()
    if not candidate:
        raise CreationError(422, "validation_error", "URL is required.")

    split = urlsplit(candidate)
    if split.scheme.lower() not in {"http", "https"} or not split.hostname:
        raise CreationError(422, "validation_error", "URL must use http or https and include a hostname.")
    return split


def normalize_url(raw_url: str) -> str:
    split = _normalized_split(raw_url)
    scheme = split.scheme.lower()
    hostname = split.hostname.lower()
    port = split.port
    netloc = hostname
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    normalized = SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=split.path,
        query=split.query,
        fragment="",
    )
    return urlunsplit(normalized)


def hostname_from_url(normalized_url: str) -> str:
    return _normalized_split(normalized_url).hostname.lower()


async def resolve_or_create_domain(*, db: AsyncSession, hostname: str) -> Domain:
    insert_stmt = (
        pg_insert(Domain)
        .values(hostname=hostname)
        .on_conflict_do_nothing(index_elements=["hostname"])
    )
    await db.execute(insert_stmt)
    domain = await db.scalar(select(Domain).where(Domain.hostname == hostname))
    if domain is None:  # pragma: no cover - defensive guard
        raise CreationError(500, "internal_error", "Failed to resolve domain.")
    return domain


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
        submitted_at=now,
        job_expires_at=payload.job_expires_at,
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

    post = await db.scalar(select(Post).where(Post.id == post_id, Post.status == PostStatus.ACTIVE))
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

    comment = Comment(
        post_id=post_id,
        author_id=author.id,
        parent_comment_id=payload.parent_comment_id,
        body_markdown=body_markdown,
        status=CommentStatus.ACTIVE,
        depth=depth,
    )
    db.add(comment)
    now = _utcnow()
    await db.flush()
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(
            comment_count=Post.comment_count + 1,
            last_commented_at=now,
        )
    )
    await db.commit()
    return await get_comment_detail(
        db=db,
        comment_id=comment.id,
        viewer_user_id=author.id,
        viewer_role=author.role,
    )
