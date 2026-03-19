from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import Category, CommentStatus, PostStatus, PostType, UserStatus
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User


@dataclass(slots=True)
class PlatformSummarySnapshot:
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


async def get_platform_summary(db: AsyncSession) -> PlatformSummarySnapshot:
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_end = month_start
    previous_month_start = (month_start - timedelta(microseconds=1)).replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    month_elapsed = now - month_start
    previous_month_comparison_end = min(previous_month_start + month_elapsed, previous_month_end)
    day_start = now - timedelta(hours=24)
    previous_day_start = now - timedelta(hours=48)
    week_start = now - timedelta(days=7)
    previous_week_start = now - timedelta(days=14)
    window_30d_start = now - timedelta(days=30)
    previous_30d_start = now - timedelta(days=60)

    builders_this_month = await _count(
        db,
        select(func.count())
        .select_from(User)
        .where(User.status == UserStatus.ACTIVE, User.created_at >= month_start),
    )
    builders_previous_month = await _count(
        db,
        select(func.count())
        .select_from(User)
        .where(
            User.status == UserStatus.ACTIVE,
            User.created_at >= previous_month_start,
            User.created_at < previous_month_comparison_end,
        ),
    )
    funding_stories_last_30d = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.category == Category.FUNDING,
            Post.submitted_at >= window_30d_start,
        ),
    )
    funding_stories_previous_30d = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.category == Category.FUNDING,
            Post.submitted_at >= previous_30d_start,
            Post.submitted_at < window_30d_start,
        ),
    )
    posts_last_day = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(Post.status == PostStatus.ACTIVE, Post.submitted_at >= day_start),
    )
    posts_previous_day = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.submitted_at >= previous_day_start,
            Post.submitted_at < day_start,
        ),
    )
    comments_this_week = await _count(
        db,
        select(func.count())
        .select_from(Comment)
        .where(Comment.status == CommentStatus.ACTIVE, Comment.created_at >= week_start),
    )
    comments_previous_week = await _count(
        db,
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.status == CommentStatus.ACTIVE,
            Comment.created_at >= previous_week_start,
            Comment.created_at < week_start,
        ),
    )
    jobs_live = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.post_type == PostType.JOB,
            or_(Post.job_expires_at.is_(None), Post.job_expires_at > now),
        ),
    )
    jobs_live_previous_week = await _count(
        db,
        select(func.count())
        .select_from(Post)
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.post_type == PostType.JOB,
            Post.submitted_at <= week_start,
            or_(Post.job_expires_at.is_(None), Post.job_expires_at > week_start),
        ),
    )

    return PlatformSummarySnapshot(
        builders_this_month=builders_this_month,
        builders_delta_pct=_percentage_change(builders_this_month, builders_previous_month),
        funding_stories_last_30d=funding_stories_last_30d,
        funding_stories_delta_pct=_percentage_change(
            funding_stories_last_30d,
            funding_stories_previous_30d,
        ),
        posts_per_hour=round(posts_last_day / 24, 1),
        posts_per_hour_delta_pct=_percentage_change(posts_last_day, posts_previous_day),
        comments_this_week=comments_this_week,
        comments_delta_pct=_percentage_change(comments_this_week, comments_previous_week),
        jobs_live=jobs_live,
        jobs_live_delta_pct=_percentage_change(jobs_live, jobs_live_previous_week),
    )


async def _count(db: AsyncSession, statement) -> int:
    return int((await db.scalar(statement)) or 0)


def _percentage_change(current: int, previous: int) -> float | None:
    if previous <= 0:
        return None
    return round(((current - previous) / previous) * 100, 1)
