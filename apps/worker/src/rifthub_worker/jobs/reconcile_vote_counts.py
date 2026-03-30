from __future__ import annotations

import logging

from rifthub_backend import get_async_session
from rifthub_backend.reconciliation import reconcile_vote_counts

logger = logging.getLogger(__name__)


async def reconcile_vote_counts_job() -> None:
    async for db in get_async_session():
        result = await reconcile_vote_counts(db=db)
        logger.info(
            "reconcile_vote_counts job completed: scanned_posts=%s updated_posts=%s scanned_comments=%s updated_comments=%s",
            result.scanned_post_count,
            result.updated_post_count,
            result.scanned_comment_count,
            result.updated_comment_count,
        )
