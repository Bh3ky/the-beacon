from __future__ import annotations

import logging

from rifthub_backend import get_async_session
from rifthub_backend.ranking_refresh import refresh_post_rank_scores

logger = logging.getLogger(__name__)


async def refresh_post_scores_job() -> None:
    async for db in get_async_session():
        result = await refresh_post_rank_scores(db=db)
        logger.info(
            "refresh_post_scores job completed: scanned=%s refreshed=%s",
            result.scanned_count,
            result.refreshed_count,
        )
