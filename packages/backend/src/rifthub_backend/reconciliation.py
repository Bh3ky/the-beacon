from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.models.comment import Comment
from rifthub_backend.models.post import Post
from rifthub_backend.models.vote import CommentVote, PostVote
from rifthub_backend.voting import compute_comment_rank_score, compute_post_rank_score


@dataclass(frozen=True, slots=True)
class VoteReconciliationResult:
    scanned_post_count: int
    updated_post_count: int
    scanned_comment_count: int
    updated_comment_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def reconcile_vote_counts(
    *,
    db: AsyncSession,
    now: datetime | None = None,
) -> VoteReconciliationResult:
    effective_now = now or _utcnow()
    post_vote_rows = await db.execute(
        select(
            PostVote.post_id,
            func.sum(case((PostVote.vote_value == 1, 1), else_=0)),
            func.sum(case((PostVote.vote_value == -1, 1), else_=0)),
        ).group_by(PostVote.post_id)
    )
    post_vote_totals = {
        post_id: (int(upvotes or 0), int(downvotes or 0))
        for post_id, upvotes, downvotes in post_vote_rows.all()
    }

    post_rows = await db.execute(select(Post).options(joinedload(Post.domain)))
    posts = post_rows.scalars().unique().all()
    updated_post_count = 0

    for post in posts:
        expected_upvotes, expected_downvotes = post_vote_totals.get(post.id, (0, 0))
        expected_score = expected_upvotes - expected_downvotes
        expected_rank_score = compute_post_rank_score(
            score=expected_score,
            submitted_at=post.submitted_at,
            comment_count=post.comment_count,
            category=post.category,
            domain_trust_score=post.domain.trust_score if post.domain is not None else None,
            now=effective_now,
        )

        if (
            post.upvote_count != expected_upvotes
            or post.downvote_count != expected_downvotes
            or post.score != expected_score
            or post.rank_score != expected_rank_score
        ):
            post.upvote_count = expected_upvotes
            post.downvote_count = expected_downvotes
            post.score = expected_score
            post.rank_score = expected_rank_score
            updated_post_count += 1

    comment_vote_rows = await db.execute(
        select(
            CommentVote.comment_id,
            func.sum(case((CommentVote.vote_value == 1, 1), else_=0)),
            func.sum(case((CommentVote.vote_value == -1, 1), else_=0)),
        ).group_by(CommentVote.comment_id)
    )
    comment_vote_totals = {
        comment_id: (int(upvotes or 0), int(downvotes or 0))
        for comment_id, upvotes, downvotes in comment_vote_rows.all()
    }

    comment_rows = await db.execute(select(Comment))
    comments = comment_rows.scalars().all()
    updated_comment_count = 0

    for comment in comments:
        expected_upvotes, expected_downvotes = comment_vote_totals.get(comment.id, (0, 0))
        expected_score = expected_upvotes - expected_downvotes
        expected_rank_score = compute_comment_rank_score(
            score=expected_score,
            created_at=comment.created_at,
            now=effective_now,
        )

        if (
            comment.upvote_count != expected_upvotes
            or comment.downvote_count != expected_downvotes
            or comment.score != expected_score
            or comment.rank_score != expected_rank_score
        ):
            comment.upvote_count = expected_upvotes
            comment.downvote_count = expected_downvotes
            comment.score = expected_score
            comment.rank_score = expected_rank_score
            updated_comment_count += 1

    if updated_post_count or updated_comment_count:
        await db.commit()

    return VoteReconciliationResult(
        scanned_post_count=len(posts),
        updated_post_count=updated_post_count,
        scanned_comment_count=len(comments),
        updated_comment_count=updated_comment_count,
    )
