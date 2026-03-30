from __future__ import annotations

from collections.abc import AsyncIterator
import logging

import pytest

import rifthub_worker.jobs.expire_job_posts as expire_job_module
from rifthub_backend.job_expiry import JobExpiryEnforcementResult


@pytest.mark.anyio
async def test_expire_job_posts_job_uses_shared_backend_policy(monkeypatch, caplog) -> None:
    fake_db = object()
    calls: list[object] = []

    async def fake_get_async_session() -> AsyncIterator[object]:
        yield fake_db

    async def fake_enforce_job_post_expiry_policy(*, db) -> JobExpiryEnforcementResult:
        calls.append(db)
        return JobExpiryEnforcementResult(scanned_count=4, updated_count=2)

    monkeypatch.setattr(expire_job_module, "get_async_session", fake_get_async_session)
    monkeypatch.setattr(expire_job_module, "enforce_job_post_expiry_policy", fake_enforce_job_post_expiry_policy)

    with caplog.at_level(logging.INFO):
        await expire_job_module.expire_job_posts_job()

    assert calls == [fake_db]
    assert "expire_job_posts job completed: scanned=4 updated=2" in caplog.text
