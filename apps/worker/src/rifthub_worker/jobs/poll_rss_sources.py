from __future__ import annotations

import logging

from rifthub_backend import get_async_session, get_settings
from rifthub_backend.ingestion_polling import SOURCE_POLL_LOCK_PREFIX, poll_due_rss_sources

logger = logging.getLogger(__name__)


def build_source_poll_lock_manager():
    from rifthub_worker.runners.locks import NoopJobExecutionLockManager, RedisJobExecutionLockManager

    settings = get_settings()
    if settings.redis_url:
        return RedisJobExecutionLockManager(
            redis_url=settings.redis_url,
            prefix=SOURCE_POLL_LOCK_PREFIX,
        )
    return NoopJobExecutionLockManager()


async def poll_rss_sources_job() -> None:
    lock_manager = build_source_poll_lock_manager()
    try:
        async for db in get_async_session():
            result = await poll_due_rss_sources(db=db, source_lock_manager=lock_manager)
            logger.info(
                "poll_rss_sources job completed: selected=%s polled=%s unchanged=%s failed=%s discovered=%s stored=%s normalized=%s duplicate=%s processed=%s published=%s awaiting_review=%s",
                result.selected_source_count,
                result.polled_source_count,
                result.unchanged_source_count,
                result.failed_source_count,
                result.discovered_entry_count,
                result.stored_item_count,
                result.normalized_item_count,
                result.duplicate_item_count,
                result.processed_item_count,
                result.published_item_count,
                result.awaiting_review_item_count,
            )
            break
    finally:
        await lock_manager.aclose()
