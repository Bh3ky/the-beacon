from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from rifthub_backend.db.types import Category
from rifthub_backend.reconciliation import reconcile_vote_counts


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def unique(self):
        return self

    def all(self):
        return self._rows


class FakeResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self):
        return self._rows

    def scalars(self):
        return FakeScalarResult(self._rows)


class FakeDbSession:
    def __init__(self, results: list[FakeResult]) -> None:
        self._results = iter(results)
        self.commit_calls = 0

    async def execute(self, _statement):
        return next(self._results)

    async def commit(self) -> None:
        self.commit_calls += 1


@pytest.mark.anyio
async def test_reconcile_vote_counts_repairs_post_and_comment_counters() -> None:
    now = datetime.now(UTC)
    post = SimpleNamespace(
        id=uuid4(),
        upvote_count=0,
        downvote_count=0,
        score=0,
        rank_score=0.0,
        submitted_at=now - timedelta(hours=2),
        comment_count=3,
        category=Category.FUNDING,
        domain=SimpleNamespace(trust_score=Decimal("1.05")),
    )
    comment = SimpleNamespace(
        id=uuid4(),
        upvote_count=0,
        downvote_count=0,
        score=0,
        rank_score=0.0,
        created_at=now - timedelta(hours=1),
    )
    db = FakeDbSession(
        [
            FakeResult([(post.id, 4, 1)]),
            FakeResult([post]),
            FakeResult([(comment.id, 3, 0)]),
            FakeResult([comment]),
        ]
    )

    result = await reconcile_vote_counts(
        db=db,  # type: ignore[arg-type]
        now=now,
    )

    assert result.scanned_post_count == 1
    assert result.updated_post_count == 1
    assert result.scanned_comment_count == 1
    assert result.updated_comment_count == 1
    assert post.upvote_count == 4
    assert post.downvote_count == 1
    assert post.score == 3
    assert post.rank_score > 0
    assert comment.upvote_count == 3
    assert comment.downvote_count == 0
    assert comment.score == 3
    assert comment.rank_score > 0
    assert db.commit_calls == 1
