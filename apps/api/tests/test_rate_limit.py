from __future__ import annotations

from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock

import redis.asyncio as redis_asyncio

from rifthub_api.errors import ApiError
from rifthub_api.rate_limit import ConfigurableRateLimiter, InMemoryRateLimiter, RedisRateLimiter
from rifthub_backend.config import Settings


@pytest.mark.anyio
async def test_in_memory_rate_limiter_allows_requests_within_window() -> None:
    limiter = InMemoryRateLimiter()

    await limiter.check(
        key="login:ip:127.0.0.1",
        limit=2,
        window_seconds=60,
        message="Too many login attempts. Try again later.",
    )
    await limiter.check(
        key="login:ip:127.0.0.1",
        limit=2,
        window_seconds=60,
        message="Too many login attempts. Try again later.",
    )


@pytest.mark.anyio
async def test_in_memory_rate_limiter_blocks_request_after_limit() -> None:
    limiter = InMemoryRateLimiter()

    await limiter.check(
        key="login:ip:127.0.0.1",
        limit=1,
        window_seconds=60,
        message="Too many login attempts. Try again later.",
    )

    with pytest.raises(ApiError) as exc_info:
        await limiter.check(
            key="login:ip:127.0.0.1",
            limit=1,
            window_seconds=60,
            message="Too many login attempts. Try again later.",
        )

    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "rate_limited"


@pytest.mark.anyio
async def test_configurable_rate_limiter_uses_in_memory_backend_for_memory_mode() -> None:
    limiter = ConfigurableRateLimiter()
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        rate_limit_backend="memory",
    )

    await limiter.configure(settings)
    await limiter.check(
        key="login:ip:127.0.0.1",
        limit=1,
        window_seconds=60,
        message="Too many login attempts. Try again later.",
    )


@pytest.mark.anyio
async def test_configurable_rate_limiter_closes_previous_backend_when_reconfigured() -> None:
    limiter = ConfigurableRateLimiter()
    previous_backend = limiter._backend
    previous_backend.aclose = AsyncMock()
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        rate_limit_backend="memory",
        rate_limit_prefix="next-prefix",
    )

    await limiter.configure(settings)

    previous_backend.aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_redis_rate_limiter_blocks_after_limit(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        eval=AsyncMock(return_value=2),
        aclose=AsyncMock(),
    )
    monkeypatch.setattr(
        redis_asyncio.Redis,
        "from_url",
        lambda redis_url, decode_responses=True: fake_client,
    )

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379/0",
        prefix="rifthub:test",
    )

    with pytest.raises(ApiError) as exc_info:
        await limiter.check(
            key="login:ip:127.0.0.1",
            limit=1,
            window_seconds=60,
            message="Too many login attempts. Try again later.",
        )

    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "rate_limited"
    fake_client.eval.assert_awaited_once()


@pytest.mark.anyio
async def test_redis_rate_limiter_ping_and_close_use_client(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        ping=AsyncMock(),
        eval=AsyncMock(return_value=1),
        aclose=AsyncMock(),
    )
    monkeypatch.setattr(
        redis_asyncio.Redis,
        "from_url",
        lambda redis_url, decode_responses=True: fake_client,
    )

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379/0",
        prefix="rifthub:test",
    )

    await limiter.ping()
    await limiter.aclose()

    fake_client.ping.assert_awaited_once()
    fake_client.aclose.assert_awaited_once()
