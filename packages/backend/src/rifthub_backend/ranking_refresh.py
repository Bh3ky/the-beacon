from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.db.types import PostStatus, PostType
from rifthub_backend.models.domain import Domain
from rifthub_backend.models.post import Post
from rifthub_backend.voting import compute_post_rank_score

POST_SCORE_REFRESH_WINDOW_HOURS = 72


@dataclass(frozen=True, slots=True)
class PostScoreRefreshResult:
    scanned_count: int
    refreshed_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def refresh_post_rank_scores(
    *,
    db: AsyncSession,
    now: datetime | None = None,
    recent_window_hours: int = POST_SCORE_REFRESH_WINDOW_HOURS,
) -> PostScoreRefreshResult:
    effective_now = now or _utcnow()
    window_start = effective_now - timedelta(hours=recent_window_hours)
    result = await db.execute(
        select(Post)
        .options(joinedload(Post.domain))
        .where(
            Post.status == PostStatus.ACTIVE,
            Post.post_type != PostType.JOB,
            or_(
                Post.submitted_at >= window_start,
                Post.last_commented_at >= window_start,
            ),
            or_(Post.domain_id.is_(None), Post.domain.has(Domain.is_blocked.is_(False))),
        )
    )
    posts = result.scalars().unique().all()

    for post in posts:
        post.rank_score = compute_post_rank_score(
            score=post.score,
            submitted_at=post.submitted_at,
            comment_count=post.comment_count,
            category=post.category,
            domain_trust_score=post.domain.trust_score if post.domain is not None else None,
            now=effective_now,
        )

    if posts:
        await db.commit()

    return PostScoreRefreshResult(scanned_count=len(posts), refreshed_count=len(posts))
