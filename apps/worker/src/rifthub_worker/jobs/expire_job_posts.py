from __future__ import annotations

import logging

from rifthub_backend import get_async_session
from rifthub_backend.job_expiry import enforce_job_post_expiry_policy

logger = logging.getLogger(__name__)


async def expire_job_posts_job() -> None:
    async for db in get_async_session():
        result = await enforce_job_post_expiry_policy(db=db)
        logger.info(
            "expire_job_posts job completed: scanned=%s updated=%s",
            result.scanned_count,
            result.updated_count,
        )
