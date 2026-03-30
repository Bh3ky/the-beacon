from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from rifthub_backend.db.types import Category
from rifthub_backend.ranking_refresh import refresh_post_rank_scores


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

    def scalars(self):
        return FakeScalarResult(self._rows)


class FakeDbSession:
    def __init__(self, posts: list[object]) -> None:
        self.posts = posts
        self.statements: list[object] = []
        self.commit_calls = 0

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult(self.posts)

    async def commit(self) -> None:
        self.commit_calls += 1


@pytest.mark.anyio
async def test_refresh_post_rank_scores_updates_recent_non_job_posts() -> None:
    now = datetime.now(UTC)
    post = SimpleNamespace(
        score=11,
        submitted_at=now - timedelta(hours=2),
        comment_count=4,
        category=Category.FUNDING,
        domain=SimpleNamespace(trust_score=Decimal("1.05")),
        rank_score=0.0,
    )
    db = FakeDbSession([post])

    result = await refresh_post_rank_scores(
        db=db,  # type: ignore[arg-type]
        now=now,
    )

    assert result.scanned_count == 1
    assert result.refreshed_count == 1
    assert post.rank_score > 0
    assert db.commit_calls == 1


@pytest.mark.anyio
async def test_refresh_post_rank_scores_query_excludes_jobs_and_blocked_domains() -> None:
    now = datetime.now(UTC)
    db = FakeDbSession([])

    await refresh_post_rank_scores(
        db=db,  # type: ignore[arg-type]
        now=now,
    )

    compiled = str(
        db.statements[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "posts.post_type != 'job'" in compiled
    assert "domains.is_blocked is false" in compiled.lower()
