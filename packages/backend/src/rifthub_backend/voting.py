from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import pow
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import CommentStatus, PostStatus
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.models.vote import CommentVote, PostVote
from rifthub_backend.write_access import user_has_restricted_write_access

POST_RANK_GRAVITY = 1.4
POST_RANK_HOURS_OFFSET = 3.0


@dataclass(slots=True)
class VotingError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


@dataclass(frozen=True, slots=True)
class VoteDelta:
    upvote_delta: int
    downvote_delta: int
    score_delta: int
    viewer_vote: int | None
    changed: bool


@dataclass(frozen=True, slots=True)
class PostVoteRead:
    id: UUID
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: int | None


@dataclass(frozen=True, slots=True)
class CommentVoteRead:
    id: UUID
    upvote_count: int
    downvote_count: int
    score: int
    rank_score: float
    viewer_vote: int | None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_user_can_vote(*, user: User) -> None:
    if user_has_restricted_write_access(status=user.status):
        raise VotingError(403, "forbidden", "Your account cannot perform this action.")


def compute_vote_delta(*, previous_vote: int | None, next_vote: int | None) -> VoteDelta:
    if previous_vote == next_vote:
        return VoteDelta(
            upvote_delta=0,
            downvote_delta=0,
            score_delta=0,
            viewer_vote=next_vote,
            changed=False,
        )

    upvote_delta = 0
    downvote_delta = 0
    score_delta = 0

    if previous_vote == 1:
        upvote_delta -= 1
        score_delta -= 1
    elif previous_vote == -1:
        downvote_delta -= 1
        score_delta += 1

    if next_vote == 1:
        upvote_delta += 1
        score_delta += 1
    elif next_vote == -1:
        downvote_delta += 1
        score_delta -= 1

    return VoteDelta(
        upvote_delta=upvote_delta,
        downvote_delta=downvote_delta,
        score_delta=score_delta,
        viewer_vote=next_vote,
        changed=True,
    )


def compute_post_rank_score(*, score: int, submitted_at: datetime, now: datetime | None = None) -> float:
    effective_now = now or _utcnow()
    age_seconds = max((effective_now - submitted_at).total_seconds(), 0.0)
    age_hours = age_seconds / 3600.0
    base_vote_score = score + 1
    return float(base_vote_score / pow(age_hours + POST_RANK_HOURS_OFFSET, POST_RANK_GRAVITY))


async def _load_active_post(*, db: AsyncSession, post_id: UUID) -> Post:
    post = await db.scalar(select(Post).where(Post.id == post_id, Post.status == PostStatus.ACTIVE))
    if post is None:
        raise VotingError(404, "post_not_found", "The requested post does not exist.")
    return post


async def _load_active_comment(*, db: AsyncSession, comment_id: UUID) -> Comment:
    comment = await db.scalar(select(Comment).where(Comment.id == comment_id, Comment.status == CommentStatus.ACTIVE))
    if comment is None:
        raise VotingError(404, "comment_not_found", "The requested comment does not exist.")
    return comment


async def _load_post_vote(*, db: AsyncSession, post_id: UUID, user_id: UUID) -> PostVote | None:
    return await db.scalar(
        select(PostVote).where(
            PostVote.post_id == post_id,
            PostVote.user_id == user_id,
        )
    )


async def _load_comment_vote(*, db: AsyncSession, comment_id: UUID, user_id: UUID) -> CommentVote | None:
    return await db.scalar(
        select(CommentVote).where(
            CommentVote.comment_id == comment_id,
            CommentVote.user_id == user_id,
        )
    )


def _post_vote_read(*, post: Post, viewer_vote: int | None) -> PostVoteRead:
    return PostVoteRead(
        id=post.id,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        score=post.score,
        rank_score=post.rank_score,
        viewer_vote=viewer_vote,
    )


def _comment_vote_read(*, comment: Comment, viewer_vote: int | None) -> CommentVoteRead:
    return CommentVoteRead(
        id=comment.id,
        upvote_count=comment.upvote_count,
        downvote_count=comment.downvote_count,
        score=comment.score,
        rank_score=comment.rank_score,
        viewer_vote=viewer_vote,
    )


def _post_vote_read_from_values(
    *,
    post_id: UUID,
    upvote_count: int,
    downvote_count: int,
    score: int,
    rank_score: float,
    viewer_vote: int | None,
) -> PostVoteRead:
    return PostVoteRead(
        id=post_id,
        upvote_count=upvote_count,
        downvote_count=downvote_count,
        score=score,
        rank_score=rank_score,
        viewer_vote=viewer_vote,
    )


def _comment_vote_read_from_values(
    *,
    comment_id: UUID,
    upvote_count: int,
    downvote_count: int,
    score: int,
    rank_score: float,
    viewer_vote: int | None,
) -> CommentVoteRead:
    return CommentVoteRead(
        id=comment_id,
        upvote_count=upvote_count,
        downvote_count=downvote_count,
        score=score,
        rank_score=rank_score,
        viewer_vote=viewer_vote,
    )


async def vote_on_post(
    *,
    db: AsyncSession,
    user: User,
    post_id: UUID,
    vote_value: int,
) -> PostVoteRead:
    ensure_user_can_vote(user=user)
    post = await _load_active_post(db=db, post_id=post_id)
    existing_vote = await _load_post_vote(db=db, post_id=post_id, user_id=user.id)
    previous_vote = existing_vote.vote_value if existing_vote is not None else None
    delta = compute_vote_delta(previous_vote=previous_vote, next_vote=vote_value)

    if not delta.changed:
        return _post_vote_read(post=post, viewer_vote=vote_value)

    now = _utcnow()
    next_upvote_count = post.upvote_count + delta.upvote_delta
    next_downvote_count = post.downvote_count + delta.downvote_delta
    next_score = post.score + delta.score_delta
    next_rank_score = compute_post_rank_score(score=next_score, submitted_at=post.submitted_at, now=now)
    if existing_vote is None:
        db.add(PostVote(post_id=post.id, user_id=user.id, vote_value=vote_value))
    else:
        existing_vote.vote_value = vote_value

    await db.execute(
        update(Post)
        .where(Post.id == post.id)
        .values(
            upvote_count=next_upvote_count,
            downvote_count=next_downvote_count,
            score=next_score,
            rank_score=next_rank_score,
            updated_at=now,
        )
    )
    await db.commit()
    return _post_vote_read_from_values(
        post_id=post.id,
        upvote_count=next_upvote_count,
        downvote_count=next_downvote_count,
        score=next_score,
        rank_score=next_rank_score,
        viewer_vote=vote_value,
    )


async def remove_post_vote(
    *,
    db: AsyncSession,
    user: User,
    post_id: UUID,
) -> PostVoteRead:
    ensure_user_can_vote(user=user)
    post = await _load_active_post(db=db, post_id=post_id)
    existing_vote = await _load_post_vote(db=db, post_id=post_id, user_id=user.id)
    previous_vote = existing_vote.vote_value if existing_vote is not None else None
    delta = compute_vote_delta(previous_vote=previous_vote, next_vote=None)

    if not delta.changed:
        return _post_vote_read(post=post, viewer_vote=None)

    now = _utcnow()
    next_upvote_count = post.upvote_count + delta.upvote_delta
    next_downvote_count = post.downvote_count + delta.downvote_delta
    next_score = post.score + delta.score_delta
    next_rank_score = compute_post_rank_score(score=next_score, submitted_at=post.submitted_at, now=now)
    await db.execute(delete(PostVote).where(PostVote.id == existing_vote.id))
    await db.execute(
        update(Post)
        .where(Post.id == post.id)
        .values(
            upvote_count=next_upvote_count,
            downvote_count=next_downvote_count,
            score=next_score,
            rank_score=next_rank_score,
            updated_at=now,
        )
    )
    await db.commit()
    return _post_vote_read_from_values(
        post_id=post.id,
        upvote_count=next_upvote_count,
        downvote_count=next_downvote_count,
        score=next_score,
        rank_score=next_rank_score,
        viewer_vote=None,
    )


async def vote_on_comment(
    *,
    db: AsyncSession,
    user: User,
    comment_id: UUID,
    vote_value: int,
) -> CommentVoteRead:
    ensure_user_can_vote(user=user)
    comment = await _load_active_comment(db=db, comment_id=comment_id)
    existing_vote = await _load_comment_vote(db=db, comment_id=comment_id, user_id=user.id)
    previous_vote = existing_vote.vote_value if existing_vote is not None else None
    delta = compute_vote_delta(previous_vote=previous_vote, next_vote=vote_value)

    if not delta.changed:
        return _comment_vote_read(comment=comment, viewer_vote=vote_value)

    now = _utcnow()
    next_upvote_count = comment.upvote_count + delta.upvote_delta
    next_downvote_count = comment.downvote_count + delta.downvote_delta
    next_score = comment.score + delta.score_delta
    next_rank_score = float(next_score)
    if existing_vote is None:
        db.add(CommentVote(comment_id=comment.id, user_id=user.id, vote_value=vote_value))
    else:
        existing_vote.vote_value = vote_value

    await db.execute(
        update(Comment)
        .where(Comment.id == comment.id)
        .values(
            upvote_count=next_upvote_count,
            downvote_count=next_downvote_count,
            score=next_score,
            rank_score=next_rank_score,
            updated_at=now,
        )
    )
    await db.commit()
    return _comment_vote_read_from_values(
        comment_id=comment.id,
        upvote_count=next_upvote_count,
        downvote_count=next_downvote_count,
        score=next_score,
        rank_score=next_rank_score,
        viewer_vote=vote_value,
    )


async def remove_comment_vote(
    *,
    db: AsyncSession,
    user: User,
    comment_id: UUID,
) -> CommentVoteRead:
    ensure_user_can_vote(user=user)
    comment = await _load_active_comment(db=db, comment_id=comment_id)
    existing_vote = await _load_comment_vote(db=db, comment_id=comment_id, user_id=user.id)
    previous_vote = existing_vote.vote_value if existing_vote is not None else None
    delta = compute_vote_delta(previous_vote=previous_vote, next_vote=None)

    if not delta.changed:
        return _comment_vote_read(comment=comment, viewer_vote=None)

    now = _utcnow()
    next_upvote_count = comment.upvote_count + delta.upvote_delta
    next_downvote_count = comment.downvote_count + delta.downvote_delta
    next_score = comment.score + delta.score_delta
    next_rank_score = float(next_score)
    await db.execute(delete(CommentVote).where(CommentVote.id == existing_vote.id))
    await db.execute(
        update(Comment)
        .where(Comment.id == comment.id)
        .values(
            upvote_count=next_upvote_count,
            downvote_count=next_downvote_count,
            score=next_score,
            rank_score=next_rank_score,
            updated_at=now,
        )
    )
    await db.commit()
    return _comment_vote_read_from_values(
        comment_id=comment.id,
        upvote_count=next_upvote_count,
        downvote_count=next_downvote_count,
        score=next_score,
        rank_score=next_rank_score,
        viewer_vote=None,
    )
