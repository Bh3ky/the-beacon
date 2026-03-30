from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

import rifthub_backend.feed_snapshots as feed_snapshot_module


def make_page(kind: str):
    return SimpleNamespace(
        items=[SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())],
        page_info=SimpleNamespace(
            next_cursor=f"{kind}-cursor",
            has_next_page=kind != "jobs",
        ),
    )


@pytest.mark.anyio
async def test_build_feed_snapshots_builds_all_feed_kinds(monkeypatch) -> None:
    now = datetime.now(UTC)

    async def fake_top_feed(**_: object):
        return make_page("top")

    async def fake_new_feed(**_: object):
        return make_page("new")

    async def fake_ask_feed(**_: object):
        return make_page("ask")

    async def fake_show_feed(**_: object):
        return make_page("show")

    async def fake_jobs_feed(**_: object):
        return make_page("jobs")

    monkeypatch.setattr(feed_snapshot_module, "get_top_feed", fake_top_feed)
    monkeypatch.setattr(feed_snapshot_module, "get_new_feed", fake_new_feed)
    monkeypatch.setattr(feed_snapshot_module, "get_ask_feed", fake_ask_feed)
    monkeypatch.setattr(feed_snapshot_module, "get_show_feed", fake_show_feed)
    monkeypatch.setattr(feed_snapshot_module, "get_jobs_feed", fake_jobs_feed)

    snapshots = await feed_snapshot_module.build_feed_snapshots(
        db=object(),  # type: ignore[arg-type]
        now=now,
    )

    assert [snapshot.kind for snapshot in snapshots] == ["top", "new", "ask", "show", "jobs"]
    assert [snapshot.ttl_seconds for snapshot in snapshots] == [60, 30, 60, 60, 300]
    assert all(snapshot.generated_at == now.isoformat() for snapshot in snapshots)
    assert all(len(snapshot.post_ids) == 2 for snapshot in snapshots)
