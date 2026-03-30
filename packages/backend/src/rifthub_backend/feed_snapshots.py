from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.reads import get_ask_feed, get_jobs_feed, get_new_feed, get_show_feed, get_top_feed

FeedSnapshotKind = Literal["top", "new", "ask", "show", "jobs"]

FEED_SNAPSHOT_LIMIT = 50
FEED_SNAPSHOT_TTLS: dict[FeedSnapshotKind, int] = {
    "top": 60,
    "new": 30,
    "ask": 60,
    "show": 60,
    "jobs": 300,
}


@dataclass(frozen=True, slots=True)
class FeedSnapshot:
    kind: FeedSnapshotKind
    generated_at: str
    ttl_seconds: int
    post_ids: list[str]
    next_cursor: str | None
    has_next_page: bool


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def build_feed_snapshots(
    *,
    db: AsyncSession,
    now: datetime | None = None,
    limit: int = FEED_SNAPSHOT_LIMIT,
) -> list[FeedSnapshot]:
    generated_at = (now or _utcnow()).isoformat()
    readers = {
        "top": get_top_feed,
        "new": get_new_feed,
        "ask": get_ask_feed,
        "show": get_show_feed,
        "jobs": get_jobs_feed,
    }
    snapshots: list[FeedSnapshot] = []

    for kind, reader in readers.items():
        page = await reader(
            db=db,
            limit=limit,
            cursor=None,
            viewer_user_id=None,
            viewer_role=None,
        )
        snapshots.append(
            FeedSnapshot(
                kind=kind,
                generated_at=generated_at,
                ttl_seconds=FEED_SNAPSHOT_TTLS[kind],
                post_ids=[str(item.id) for item in page.items],
                next_cursor=page.page_info.next_cursor,
                has_next_page=page.page_info.has_next_page,
            )
        )

    return snapshots
