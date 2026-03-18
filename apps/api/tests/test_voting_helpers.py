from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from rifthub_backend.voting import (
    CommentVoteRead,
    PostVoteRead,
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
