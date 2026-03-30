from __future__ import annotations

from collections.abc import AsyncIterator
import logging

import pytest

import rifthub_worker.jobs.poll_rss_sources as poll_job_module
from rifthub_backend.ingestion_polling import PollSourcesResult


@pytest.mark.anyio
async def test_poll_rss_sources_job_uses_shared_backend_service(monkeypatch, caplog) -> None:
    fake_db = object()
    calls: list[object] = []

    async def fake_get_async_session() -> AsyncIterator[object]:
        yield fake_db

    async def fake_poll_due_rss_sources(**kwargs):
        calls.append(kwargs["db"])
        assert kwargs["source_lock_manager"] is lock_manager
        return PollSourcesResult(
            selected_source_count=4,
            polled_source_count=2,
            unchanged_source_count=1,
            failed_source_count=1,
            discovered_entry_count=12,
            stored_item_count=10,
            normalized_item_count=7,
            duplicate_item_count=3,
            processed_item_count=8,
            published_item_count=5,
            awaiting_review_item_count=3,
        )

    class FakeLockManager:
        async def aclose(self) -> None:
            return None

    lock_manager = FakeLockManager()

    monkeypatch.setattr(poll_job_module, "get_async_session", fake_get_async_session)
    monkeypatch.setattr(poll_job_module, "poll_due_rss_sources", fake_poll_due_rss_sources)
    monkeypatch.setattr(poll_job_module, "build_source_poll_lock_manager", lambda: lock_manager)

    with caplog.at_level(logging.INFO):
        await poll_job_module.poll_rss_sources_job()

    assert calls == [fake_db]
    assert (
        "poll_rss_sources job completed: selected=4 polled=2 unchanged=1 failed=1 discovered=12 stored=10 normalized=7 duplicate=3 processed=8 published=5 awaiting_review=3"
        in caplog.text
    )
