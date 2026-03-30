from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from rifthub_backend.db.types import PostType
from rifthub_backend.job_expiry import (
    JOB_POST_EXPIRY_DAYS,
    bounded_job_expiry,
    enforce_job_post_expiry_policy,
    normalize_new_job_expiry,
)


def test_normalize_new_job_expiry_defaults_to_thirty_days_for_jobs() -> None:
    now = datetime.now(UTC)

    assert normalize_new_job_expiry(
        post_type=PostType.JOB,
        requested_job_expires_at=None,
        now=now,
    ) == now + timedelta(days=JOB_POST_EXPIRY_DAYS)


def test_normalize_new_job_expiry_rejects_non_job_expiry() -> None:
    with pytest.raises(ValueError, match="only allowed for job posts"):
        normalize_new_job_expiry(
            post_type=PostType.TEXT,
            requested_job_expires_at=datetime.now(UTC) + timedelta(days=1),
            now=datetime.now(UTC),
        )


def test_normalize_new_job_expiry_rejects_past_value() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="must be in the future"):
        normalize_new_job_expiry(
            post_type=PostType.JOB,
            requested_job_expires_at=now - timedelta(minutes=1),
            now=now,
        )


def test_normalize_new_job_expiry_rejects_more_than_thirty_days() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="cannot be more than 30 days"):
        normalize_new_job_expiry(
            post_type=PostType.JOB,
            requested_job_expires_at=now + timedelta(days=JOB_POST_EXPIRY_DAYS, minutes=1),
            now=now,
        )


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

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
        self.commit_calls = 0

    async def execute(self, _statement):
        return FakeResult(self.posts)

    async def commit(self) -> None:
        self.commit_calls += 1


@pytest.mark.anyio
async def test_enforce_job_post_expiry_policy_backfills_missing_and_clamps_long_expiry() -> None:
    now = datetime.now(UTC)
    missing_expiry = SimpleNamespace(
        submitted_at=now - timedelta(days=3),
        job_expires_at=None,
    )
    long_expiry = SimpleNamespace(
        submitted_at=now - timedelta(days=2),
        job_expires_at=now + timedelta(days=90),
    )
    valid_expiry = SimpleNamespace(
        submitted_at=now - timedelta(days=1),
        job_expires_at=now + timedelta(days=5),
    )
    db = FakeDbSession([missing_expiry, long_expiry, valid_expiry])

    result = await enforce_job_post_expiry_policy(
        db=db,  # type: ignore[arg-type]
        now=now,
    )

    assert result.scanned_count == 3
    assert result.updated_count == 2
    assert missing_expiry.job_expires_at == bounded_job_expiry(submitted_at=missing_expiry.submitted_at)
    assert long_expiry.job_expires_at == bounded_job_expiry(submitted_at=long_expiry.submitted_at)
    assert valid_expiry.job_expires_at == now + timedelta(days=5)
    assert db.commit_calls == 1
