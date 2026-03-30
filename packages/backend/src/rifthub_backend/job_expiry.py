from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import PostStatus, PostType
from rifthub_backend.models.post import Post

JOB_POST_EXPIRY_DAYS = 30


@dataclass(frozen=True, slots=True)
class JobExpiryEnforcementResult:
    scanned_count: int
    updated_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def bounded_job_expiry(*, submitted_at: datetime) -> datetime:
    return _coerce_utc(submitted_at) + timedelta(days=JOB_POST_EXPIRY_DAYS)


def normalize_new_job_expiry(
    *,
    post_type: PostType,
    requested_job_expires_at: datetime | None,
    now: datetime | None = None,
) -> datetime | None:
    effective_now = now or _utcnow()
    max_expiry = bounded_job_expiry(submitted_at=effective_now)

    if post_type != PostType.JOB:
        if requested_job_expires_at is not None:
            raise ValueError("job_expires_at is only allowed for job posts.")
        return None

    if requested_job_expires_at is None:
        return max_expiry

    normalized_expiry = _coerce_utc(requested_job_expires_at)
    if normalized_expiry <= effective_now:
        raise ValueError("job_expires_at must be in the future.")
    if normalized_expiry > max_expiry:
        raise ValueError(f"job_expires_at cannot be more than {JOB_POST_EXPIRY_DAYS} days in the future.")
    return normalized_expiry


async def enforce_job_post_expiry_policy(
    *,
    db: AsyncSession,
    now: datetime | None = None,
) -> JobExpiryEnforcementResult:
    result = await db.execute(
        select(Post).where(
            Post.status == PostStatus.ACTIVE,
            Post.post_type == PostType.JOB,
        )
    )
    posts = result.scalars().all()
    updated_count = 0

    for post in posts:
        desired_expiry = bounded_job_expiry(submitted_at=post.submitted_at)
        current_expiry = _coerce_utc(post.job_expires_at) if post.job_expires_at is not None else None

        if current_expiry is None or current_expiry > desired_expiry:
            post.job_expires_at = desired_expiry
            updated_count += 1

    if updated_count:
        await db.commit()

    return JobExpiryEnforcementResult(scanned_count=len(posts), updated_count=updated_count)
