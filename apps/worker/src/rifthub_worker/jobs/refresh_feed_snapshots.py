from __future__ import annotations

import json
import logging

from rifthub_backend import get_async_session, get_settings
from rifthub_backend.feed_snapshots import FeedSnapshot, build_feed_snapshots

logger = logging.getLogger(__name__)

FEED_SNAPSHOT_PREFIX = "rifthub:feed-snapshot"


class RedisFeedSnapshotStore:
    def __init__(self, *, redis_url: str, prefix: str) -> None:
        if not redis_url:
            raise RuntimeError("RIFTHUB_REDIS_URL is required for feed snapshot refresh.")
        try:
            from redis.asyncio import Redis
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env packaging
            raise RuntimeError("redis package is required for feed snapshot refresh.") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._prefix = prefix

    async def write_snapshot(self, snapshot: FeedSnapshot) -> None:
        await self._client.set(
            self.snapshot_key(snapshot.kind),
            json.dumps(
                {
                    "kind": snapshot.kind,
                    "generated_at": snapshot.generated_at,
                    "ttl_seconds": snapshot.ttl_seconds,
                    "post_ids": snapshot.post_ids,
                    "next_cursor": snapshot.next_cursor,
                    "has_next_page": snapshot.has_next_page,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            ex=snapshot.ttl_seconds,
        )

    def snapshot_key(self, kind: str) -> str:
        return f"{self._prefix}:{kind}"

    async def aclose(self) -> None:
        await self._client.aclose()


async def refresh_feed_snapshots_job() -> None:
    settings = get_settings()
    store = RedisFeedSnapshotStore(redis_url=settings.redis_url, prefix=FEED_SNAPSHOT_PREFIX)
    try:
        async for db in get_async_session():
            snapshots = await build_feed_snapshots(db=db)
            break
        else:  # pragma: no cover - defensive guard
            snapshots = []

        for snapshot in snapshots:
            await store.write_snapshot(snapshot)

        logger.info("refresh_feed_snapshots job completed: snapshots=%s", len(snapshots))
    finally:
        await store.aclose()
