from __future__ import annotations

import logging

import pytest

from rifthub_worker.runners.scheduler import JobSpec, build_default_job_specs, create_scheduler_state, run_due_jobs


def test_build_default_job_specs_registers_phase_six_jobs() -> None:
    jobs = build_default_job_specs()

    assert [job.name for job in jobs] == [
        "poll_rss_sources",
        "refresh_post_scores",
        "refresh_feed_snapshots",
        "reconcile_vote_counts",
        "expire_job_posts",
    ]


@pytest.mark.anyio
async def test_run_due_jobs_executes_ready_jobs_and_reschedules() -> None:
    executions: list[str] = []

    async def first_job() -> None:
        executions.append("first")

    async def second_job() -> None:
        executions.append("second")

    state = create_scheduler_state(
        jobs=[
            JobSpec(name="first", interval_seconds=10.0, runner=first_job),
            JobSpec(name="second", interval_seconds=20.0, runner=second_job),
        ],
        now=100.0,
    )

    await run_due_jobs(state=state, now=100.0)

    assert executions == ["first", "second"]
    assert state[0].next_run_at == 110.0
    assert state[1].next_run_at == 120.0


@pytest.mark.anyio
async def test_run_due_jobs_logs_failure_and_continues(caplog) -> None:
    executions: list[str] = []

    async def failing_job() -> None:
        executions.append("failing")
        raise RuntimeError("boom")

    async def succeeding_job() -> None:
        executions.append("succeeding")

    state = create_scheduler_state(
        jobs=[
            JobSpec(name="failing", interval_seconds=10.0, runner=failing_job),
            JobSpec(name="succeeding", interval_seconds=10.0, runner=succeeding_job),
        ],
        now=50.0,
    )

    with caplog.at_level(logging.INFO):
        await run_due_jobs(state=state, now=50.0)

    assert executions == ["failing", "succeeding"]
    assert "worker job failed: failing" in caplog.text
    assert "worker job success: succeeding" in caplog.text


@pytest.mark.anyio
async def test_run_due_jobs_skips_job_when_lock_is_already_held(caplog) -> None:
    executions: list[str] = []

    async def blocked_job() -> None:
        executions.append("blocked")

    class FakeLockManager:
        async def acquire(self, *, job_name: str, lease_seconds: int):
            assert job_name == "blocked"
            assert lease_seconds == 60
            return None

        async def aclose(self) -> None:
            return None

    state = create_scheduler_state(
        jobs=[JobSpec(name="blocked", interval_seconds=10.0, runner=blocked_job)],
        now=25.0,
    )

    with caplog.at_level(logging.INFO):
        await run_due_jobs(state=state, now=25.0, lock_manager=FakeLockManager())

    assert executions == []
    assert state[0].next_run_at == 35.0
    assert "worker job skipped due to active lock: blocked" in caplog.text


@pytest.mark.anyio
async def test_run_due_jobs_releases_lock_after_execution() -> None:
    events: list[str] = []

    async def job() -> None:
        events.append("ran")

    class FakeLease:
        async def release(self) -> None:
            events.append("released")

    class FakeLockManager:
        async def acquire(self, *, job_name: str, lease_seconds: int):
            assert job_name == "refresh"
            assert lease_seconds == 60
            events.append("acquired")
            return FakeLease()

        async def aclose(self) -> None:
            return None

    state = create_scheduler_state(
        jobs=[JobSpec(name="refresh", interval_seconds=15.0, runner=job)],
        now=10.0,
    )

    await run_due_jobs(state=state, now=10.0, lock_manager=FakeLockManager())

    assert events == ["acquired", "ran", "released"]
