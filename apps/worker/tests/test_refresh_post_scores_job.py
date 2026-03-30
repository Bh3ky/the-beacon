from __future__ import annotations

from collections.abc import AsyncIterator
import logging

import pytest

import rifthub_worker.jobs.refresh_post_scores as refresh_job_module
from rifthub_backend.ranking_refresh import PostScoreRefreshResult


@pytest.mark.anyio
async def test_refresh_post_scores_job_uses_shared_backend_refresh(monkeypatch, caplog) -> None:
    fake_db = object()
    calls: list[object] = []

    async def fake_get_async_session() -> AsyncIterator[object]:
        yield fake_db

    async def fake_refresh_post_rank_scores(*, db) -> PostScoreRefreshResult:
        calls.append(db)
        return PostScoreRefreshResult(scanned_count=5, refreshed_count=5)

    monkeypatch.setattr(refresh_job_module, "get_async_session", fake_get_async_session)
    monkeypatch.setattr(refresh_job_module, "refresh_post_rank_scores", fake_refresh_post_rank_scores)

    with caplog.at_level(logging.INFO):
        await refresh_job_module.refresh_post_scores_job()

    assert calls == [fake_db]
    assert "refresh_post_scores job completed: scanned=5 refreshed=5" in caplog.text
