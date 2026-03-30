from __future__ import annotations

from dataclasses import dataclass
import asyncio
import logging
import math
import time
from collections.abc import Awaitable, Callable

from rifthub_worker.jobs import (
    expire_job_posts_job,
    poll_rss_sources_job,
    reconcile_vote_counts_job,
    refresh_feed_snapshots_job,
    refresh_post_scores_job,
)
from rifthub_worker.runners.locks import JobExecutionLockManager, NoopJobExecutionLockManager, build_job_execution_lock_manager

logger = logging.getLogger(__name__)

JobRunner = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class JobSpec:
    name: str
    interval_seconds: float
    runner: JobRunner
    lock_ttl_seconds: int | None = None


@dataclass(slots=True)
class SchedulerState:
    job: JobSpec
    next_run_at: float


@dataclass(frozen=True, slots=True)
class SchedulerClock:
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


def build_default_job_specs() -> list[JobSpec]:
    return [
        JobSpec(name="poll_rss_sources", interval_seconds=300.0, runner=poll_rss_sources_job),
        JobSpec(name="refresh_post_scores", interval_seconds=60.0, runner=refresh_post_scores_job),
        JobSpec(name="refresh_feed_snapshots", interval_seconds=60.0, runner=refresh_feed_snapshots_job),
        JobSpec(name="reconcile_vote_counts", interval_seconds=3600.0, runner=reconcile_vote_counts_job),
        JobSpec(name="expire_job_posts", interval_seconds=3600.0, runner=expire_job_posts_job),
    ]


def create_scheduler_state(*, jobs: list[JobSpec], now: float) -> list[SchedulerState]:
    return [SchedulerState(job=job, next_run_at=now) for job in jobs]


def effective_job_lock_ttl_seconds(job: JobSpec) -> int:
    if job.lock_ttl_seconds is not None:
        return job.lock_ttl_seconds
    return max(math.ceil(job.interval_seconds * 4), 60)


async def run_due_jobs(
    *,
    state: list[SchedulerState],
    now: float | None = None,
    lock_manager: JobExecutionLockManager | None = None,
) -> None:
    current_time = time.monotonic() if now is None else now
    job_lock_manager = lock_manager or NoopJobExecutionLockManager()

    for job_state in state:
        if job_state.next_run_at > current_time:
            continue

        lease = await job_lock_manager.acquire(
            job_name=job_state.job.name,
            lease_seconds=effective_job_lock_ttl_seconds(job_state.job),
        )
        if lease is None:
            logger.info("worker job skipped due to active lock: %s", job_state.job.name)
            job_state.next_run_at = current_time + job_state.job.interval_seconds
            continue

        logger.info("worker job start: %s", job_state.job.name)
        try:
            await job_state.job.runner()
        except Exception:
            logger.exception("worker job failed: %s", job_state.job.name)
        else:
            logger.info("worker job success: %s", job_state.job.name)
        finally:
            try:
                await lease.release()
            except Exception:
                logger.exception("worker job lock release failed: %s", job_state.job.name)
            job_state.next_run_at = current_time + job_state.job.interval_seconds


async def run_scheduler(
    *,
    jobs: list[JobSpec] | None = None,
    tick_seconds: float = 1.0,
    iterations: int | None = None,
    clock: SchedulerClock | None = None,
    lock_manager: JobExecutionLockManager | None = None,
) -> None:
    scheduler_clock = clock or SchedulerClock()
    job_specs = jobs or build_default_job_specs()
    state = create_scheduler_state(jobs=job_specs, now=scheduler_clock.monotonic())
    job_lock_manager = lock_manager or build_job_execution_lock_manager()

    try:
        completed_iterations = 0
        while True:
            await run_due_jobs(
                state=state,
                now=scheduler_clock.monotonic(),
                lock_manager=job_lock_manager,
            )
            completed_iterations += 1
            if iterations is not None and completed_iterations >= iterations:
                return
            await scheduler_clock.sleep(tick_seconds)
    finally:
        await job_lock_manager.aclose()
