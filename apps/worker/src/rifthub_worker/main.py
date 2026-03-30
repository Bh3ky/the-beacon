from __future__ import annotations

import asyncio
import logging

from rifthub_backend import configure_logging, get_settings
from rifthub_worker.runners import (
    build_default_job_specs,
    build_job_execution_lock_manager,
    create_scheduler_state,
    run_due_jobs,
    run_scheduler,
)

logger = logging.getLogger(__name__)


async def run_once() -> None:
    jobs = build_default_job_specs()
    logger.info("Running worker once with %s registered jobs", len(jobs))
    job_lock_manager = build_job_execution_lock_manager()
    try:
        await run_due_jobs(
            state=create_scheduler_state(jobs=jobs, now=0.0),
            now=0.0,
            lock_manager=job_lock_manager,
        )
    finally:
        await job_lock_manager.aclose()


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting RiftHub worker in %s", settings.environment)
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
