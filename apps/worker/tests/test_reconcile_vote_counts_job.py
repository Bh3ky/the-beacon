from __future__ import annotations

from collections.abc import AsyncIterator
import logging

import pytest

import rifthub_worker.jobs.reconcile_vote_counts as reconcile_job_module
from rifthub_backend.reconciliation import VoteReconciliationResult


@pytest.mark.anyio
async def test_reconcile_vote_counts_job_uses_shared_backend_reconciliation(monkeypatch, caplog) -> None:
    fake_db = object()
    calls: list[object] = []

    async def fake_get_async_session() -> AsyncIterator[object]:
        yield fake_db

    async def fake_reconcile_vote_counts(*, db) -> VoteReconciliationResult:
        calls.append(db)
        return VoteReconciliationResult(
            scanned_post_count=4,
            updated_post_count=1,
            scanned_comment_count=7,
            updated_comment_count=2,
        )

    monkeypatch.setattr(reconcile_job_module, "get_async_session", fake_get_async_session)
    monkeypatch.setattr(reconcile_job_module, "reconcile_vote_counts", fake_reconcile_vote_counts)

    with caplog.at_level(logging.INFO):
        await reconcile_job_module.reconcile_vote_counts_job()

    assert calls == [fake_db]
    assert "reconcile_vote_counts job completed: scanned_posts=4 updated_posts=1 scanned_comments=7 updated_comments=2" in caplog.text
