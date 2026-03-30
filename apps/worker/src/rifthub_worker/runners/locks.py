from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol
from uuid import uuid4

from rifthub_backend import get_settings

logger = logging.getLogger(__name__)

DEFAULT_WORKER_LOCK_PREFIX = "rifthub:worker-lock"

_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
""".strip()


class JobExecutionLease(Protocol):
    async def release(self) -> None: ...


class JobExecutionLockManager(Protocol):
    async def acquire(self, *, job_name: str, lease_seconds: int) -> JobExecutionLease | None: ...

    async def aclose(self) -> None: ...


@dataclass(frozen=True, slots=True)
class NoopJobExecutionLease:
    async def release(self) -> None:
        return None


class NoopJobExecutionLockManager:
    async def acquire(self, *, job_name: str, lease_seconds: int) -> JobExecutionLease:
        return NoopJobExecutionLease()

    async def aclose(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class RedisJobExecutionLease:
    client: Any
    key: str
    token: str

    async def release(self) -> None:
        await self.client.eval(_RELEASE_LOCK_SCRIPT, 1, self.key, self.token)


class RedisJobExecutionLockManager:
    def __init__(self, *, redis_url: str, prefix: str = DEFAULT_WORKER_LOCK_PREFIX, client: Any | None = None) -> None:
        if not redis_url and client is None:
            raise RuntimeError("RIFTHUB_REDIS_URL is required for worker job locks.")

        self._client = client if client is not None else self._build_client(redis_url)
        self._prefix = prefix

    async def acquire(self, *, job_name: str, lease_seconds: int) -> JobExecutionLease | None:
        token = uuid4().hex
        acquired = await self._client.set(
            self.lock_key(job_name),
            token,
            ex=lease_seconds,
            nx=True,
        )
        if not acquired:
            return None
        return RedisJobExecutionLease(client=self._client, key=self.lock_key(job_name), token=token)

    def lock_key(self, job_name: str) -> str:
        return f"{self._prefix}:{job_name}"

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _build_client(redis_url: str) -> Any:
        try:
            from redis.asyncio import Redis
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env packaging
            raise RuntimeError("redis package is required for worker job locks.") from exc

        return Redis.from_url(redis_url, decode_responses=True)


def build_job_execution_lock_manager() -> JobExecutionLockManager:
    settings = get_settings()
    if settings.redis_url:
        return RedisJobExecutionLockManager(redis_url=settings.redis_url)

    logger.info("worker job locks disabled: running without Redis-backed duplicate execution control")
    return NoopJobExecutionLockManager()
