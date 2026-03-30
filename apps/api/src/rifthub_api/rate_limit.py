from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import asyncio
import time

from rifthub_backend.config import Settings

from .errors import ApiError

_REDIS_FIXED_WINDOW_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
return current
"""


class RateLimiterBackend:
    async def check(self, *, key: str, limit: int, window_seconds: int, message: str) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None


@dataclass
class _WindowState:
    hits: deque[float] = field(default_factory=deque)


class InMemoryRateLimiter(RateLimiterBackend):
    def __init__(self) -> None:
        self._state: dict[str, _WindowState] = {}
        self._lock = asyncio.Lock()

    async def check(self, *, key: str, limit: int, window_seconds: int, message: str) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds

        async with self._lock:
            window = self._state.setdefault(key, _WindowState())
            while window.hits and window.hits[0] <= cutoff:
                window.hits.popleft()

            if len(window.hits) >= limit:
                raise ApiError(
                    status_code=429,
                    code="rate_limited",
                    message=message,
                )

            window.hits.append(now)


class RedisRateLimiter(RateLimiterBackend):
    def __init__(self, *, redis_url: str, prefix: str) -> None:
        try:
            from redis.asyncio import Redis
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env packaging
            raise RuntimeError("redis package is required for redis rate limiting.") from exc

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._prefix = prefix

    async def ping(self) -> None:
        await self._client.ping()

    async def check(self, *, key: str, limit: int, window_seconds: int, message: str) -> None:
        namespaced_key = f"{self._prefix}:{key}"
        hits = await self._client.eval(
            _REDIS_FIXED_WINDOW_SCRIPT,
            1,
            namespaced_key,
            str(window_seconds),
        )
        if int(hits) > limit:
            raise ApiError(
                status_code=429,
                code="rate_limited",
                message=message,
            )

    async def aclose(self) -> None:
        await self._client.aclose()


class ConfigurableRateLimiter:
    def __init__(self) -> None:
        self._backend: RateLimiterBackend = InMemoryRateLimiter()
        self._config_key = ("memory", "", "rifthub:rate-limit")
        self._lock = asyncio.Lock()

    async def configure(self, settings: Settings) -> None:
        next_config_key = (
            settings.rate_limit_backend,
            settings.redis_url,
            settings.rate_limit_prefix,
        )
        if next_config_key == self._config_key:
            return

        async with self._lock:
            if next_config_key == self._config_key:
                return

            previous_backend = self._backend
            next_backend = self._build_backend(settings)

            try:
                if isinstance(next_backend, RedisRateLimiter):
                    await next_backend.ping()
            except Exception:
                await next_backend.aclose()
                raise

            self._backend = next_backend
            self._config_key = next_config_key
            await previous_backend.aclose()

    def _build_backend(self, settings: Settings) -> RateLimiterBackend:
        if settings.rate_limit_backend == "memory":
            return InMemoryRateLimiter()
        if settings.rate_limit_backend == "redis":
            return RedisRateLimiter(
                redis_url=settings.redis_url,
                prefix=settings.rate_limit_prefix,
            )
        raise RuntimeError(f"Unsupported rate limit backend: {settings.rate_limit_backend}")

    async def check(self, *, key: str, limit: int, window_seconds: int, message: str) -> None:
        await self._backend.check(
            key=key,
            limit=limit,
            window_seconds=window_seconds,
            message=message,
        )

    async def aclose(self) -> None:
        await self._backend.aclose()
        self._backend = InMemoryRateLimiter()
        self._config_key = ("memory", "", "rifthub:rate-limit")


rate_limiter = ConfigurableRateLimiter()
