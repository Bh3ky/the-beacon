from __future__ import annotations

from decimal import Decimal
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

import rifthub_backend.voting as voting_module
from rifthub_backend.db.types import Category, UserStatus
from rifthub_backend.voting import (
    CommentVoteRead,
    PostVoteRead,
    compute_comment_rank_score,
    compute_post_rank_score,
    compute_vote_delta,
)


def test_compute_vote_delta_for_replacement_from_upvote_to_downvote() -> None:
    delta = compute_vote_delta(previous_vote=1, next_vote=-1)

    assert delta.upvote_delta == -1
    assert delta.downvote_delta == 1
    assert delta.score_delta == -2
    assert delta.viewer_vote == -1
    assert delta.changed is True


def test_compute_vote_delta_for_delete_from_downvote() -> None:
    delta = compute_vote_delta(previous_vote=-1, next_vote=None)

    assert delta.upvote_delta == 0
    assert delta.downvote_delta == -1
    assert delta.score_delta == 1
    assert delta.viewer_vote is None
    assert delta.changed is True


def test_compute_vote_delta_same_value_is_noop() -> None:
    delta = compute_vote_delta(previous_vote=1, next_vote=1)

    assert delta.upvote_delta == 0
    assert delta.downvote_delta == 0
    assert delta.score_delta == 0
    assert delta.viewer_vote == 1
    assert delta.changed is False


def test_compute_post_rank_score_decays_with_age() -> None:
    now = datetime.now(UTC)
    fresh_score = compute_post_rank_score(score=10, submitted_at=now - timedelta(minutes=5), now=now)
    stale_score = compute_post_rank_score(score=10, submitted_at=now - timedelta(hours=12), now=now)

    assert fresh_score > stale_score


def test_compute_post_rank_score_gives_new_posts_a_nonzero_baseline() -> None:
    now = datetime.now(UTC)

    assert compute_post_rank_score(score=0, submitted_at=now, now=now) > 0


def test_compute_post_rank_score_applies_comment_category_and_domain_adjustments() -> None:
    now = datetime.now(UTC)
    baseline = compute_post_rank_score(score=5, submitted_at=now - timedelta(hours=2), now=now)
    boosted = compute_post_rank_score(
        score=5,
        submitted_at=now - timedelta(hours=2),
        comment_count=8,
        category=Category.FUNDING,
        domain_trust_score=Decimal("1.05"),
        now=now,
    )

    assert boosted > baseline


def test_compute_comment_rank_score_decays_with_age() -> None:
    now = datetime.now(UTC)
    fresh_score = compute_comment_rank_score(score=3, created_at=now - timedelta(minutes=10), now=now)
    stale_score = compute_comment_rank_score(score=3, created_at=now - timedelta(hours=10), now=now)

    assert fresh_score > stale_score


@pytest.mark.anyio
async def test_vote_on_post_rejects_self_vote(monkeypatch) -> None:
    user_id = uuid4()

    async def fake_load_active_post(**_: object):
        return SimpleNamespace(id=uuid4(), author_id=user_id)

    monkeypatch.setattr(voting_module, "_load_active_post", fake_load_active_post)

    with pytest.raises(voting_module.VotingError, match="own content"):
        await voting_module.vote_on_post(
            db=SimpleNamespace(),  # type: ignore[arg-type]
            user=SimpleNamespace(id=user_id, status=UserStatus.ACTIVE),  # type: ignore[arg-type]
            post_id=uuid4(),
            vote_value=1,
        )


@pytest.mark.anyio
async def test_vote_on_comment_rejects_self_vote(monkeypatch) -> None:
    user_id = uuid4()

    async def fake_load_active_comment(**_: object):
        return SimpleNamespace(id=uuid4(), author_id=user_id)

    monkeypatch.setattr(voting_module, "_load_active_comment", fake_load_active_comment)

    with pytest.raises(voting_module.VotingError, match="own content"):
        await voting_module.vote_on_comment(
            db=SimpleNamespace(),  # type: ignore[arg-type]
            user=SimpleNamespace(id=user_id, status=UserStatus.ACTIVE),  # type: ignore[arg-type]
            comment_id=uuid4(),
            vote_value=1,
        )


def test_vote_read_dataclasses_preserve_minimal_payload_shape() -> None:
    post_payload = PostVoteRead(
        id=uuid4(),
        upvote_count=4,
        downvote_count=1,
        score=3,
        rank_score=1.5,
        viewer_vote=1,
    )
    comment_payload = CommentVoteRead(
        id=uuid4(),
        upvote_count=5,
        downvote_count=0,
        score=5,
        rank_score=5.0,
        viewer_vote=None,
    )

    assert post_payload.viewer_vote == 1
    assert comment_payload.rank_score == 5.0
