from __future__ import annotations

import pytest

from rifthub_worker.runners.locks import (
    DEFAULT_WORKER_LOCK_PREFIX,
    NoopJobExecutionLockManager,
    RedisJobExecutionLockManager,
    build_job_execution_lock_manager,
)


class FakeRedisClient:
    def __init__(self, *, acquire_result: bool = True) -> None:
        self.acquire_result = acquire_result
        self.set_calls: list[tuple[str, str, int, bool]] = []
        self.eval_calls: list[tuple[str, int, str, str]] = []
        self.closed = False

    async def set(self, key: str, value: str, *, ex: int, nx: bool) -> bool:
        self.set_calls.append((key, value, ex, nx))
        return self.acquire_result

    async def eval(self, script: str, num_keys: int, key: str, token: str) -> int:
        self.eval_calls.append((script, num_keys, key, token))
        return 1

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.anyio
async def test_redis_job_execution_lock_manager_acquires_and_releases_owner_token() -> None:
    client = FakeRedisClient()
    manager = RedisJobExecutionLockManager(
        redis_url="redis://localhost:6379/0",
        prefix=DEFAULT_WORKER_LOCK_PREFIX,
        client=client,
    )

    lease = await manager.acquire(job_name="refresh_post_scores", lease_seconds=120)

    assert lease is not None
    assert client.set_calls[0][0] == "rifthub:worker-lock:refresh_post_scores"
    assert client.set_calls[0][2:] == (120, True)

    await lease.release()
    await manager.aclose()

    assert client.eval_calls[0][1] == 1
    assert client.eval_calls[0][2] == "rifthub:worker-lock:refresh_post_scores"
    assert client.eval_calls[0][3] == client.set_calls[0][1]
    assert client.closed is True


@pytest.mark.anyio
async def test_redis_job_execution_lock_manager_returns_none_when_lock_is_held() -> None:
    manager = RedisJobExecutionLockManager(
        redis_url="redis://localhost:6379/0",
        client=FakeRedisClient(acquire_result=False),
    )

    lease = await manager.acquire(job_name="refresh_feed_snapshots", lease_seconds=240)

    assert lease is None


def test_build_job_execution_lock_manager_falls_back_to_noop_without_redis(monkeypatch) -> None:
    monkeypatch.setattr(
        "rifthub_worker.runners.locks.get_settings",
        lambda: type("Settings", (), {"redis_url": ""})(),
    )

    manager = build_job_execution_lock_manager()

    assert isinstance(manager, NoopJobExecutionLockManager)
