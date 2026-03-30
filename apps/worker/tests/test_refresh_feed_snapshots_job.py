from __future__ import annotations

from collections.abc import AsyncIterator
import logging

import pytest

import rifthub_worker.jobs.refresh_feed_snapshots as snapshot_job_module
from rifthub_backend.feed_snapshots import FeedSnapshot


@pytest.mark.anyio
async def test_refresh_feed_snapshots_job_writes_all_snapshots(monkeypatch, caplog) -> None:
    fake_db = object()
    written: list[FeedSnapshot] = []

    async def fake_get_async_session() -> AsyncIterator[object]:
        yield fake_db

    async def fake_build_feed_snapshots(*, db) -> list[FeedSnapshot]:
        assert db is fake_db
        return [
            FeedSnapshot(
                kind="top",
                generated_at="2026-03-24T12:00:00+00:00",
                ttl_seconds=60,
                post_ids=["a", "b"],
                next_cursor="cursor-1",
                has_next_page=True,
            ),
            FeedSnapshot(
                kind="jobs",
                generated_at="2026-03-24T12:00:00+00:00",
                ttl_seconds=300,
                post_ids=["c"],
                next_cursor=None,
                has_next_page=False,
            ),
        ]

    class FakeStore:
        def __init__(self, *, redis_url: str, prefix: str) -> None:
            assert redis_url == "redis://localhost:6379/0"
            assert prefix == snapshot_job_module.FEED_SNAPSHOT_PREFIX

        async def write_snapshot(self, snapshot: FeedSnapshot) -> None:
            written.append(snapshot)

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(snapshot_job_module, "get_async_session", fake_get_async_session)
    monkeypatch.setattr(snapshot_job_module, "build_feed_snapshots", fake_build_feed_snapshots)
    monkeypatch.setattr(snapshot_job_module, "RedisFeedSnapshotStore", FakeStore)
    monkeypatch.setattr(
        snapshot_job_module,
        "get_settings",
        lambda: type("Settings", (), {"redis_url": "redis://localhost:6379/0"})(),
    )

    with caplog.at_level(logging.INFO):
        await snapshot_job_module.refresh_feed_snapshots_job()

    assert [snapshot.kind for snapshot in written] == ["top", "jobs"]
    assert "refresh_feed_snapshots job completed: snapshots=2" in caplog.text
