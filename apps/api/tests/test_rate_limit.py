from __future__ import annotations

import pytest

from rifthub_api.errors import ApiError
from rifthub_api.rate_limit import InMemoryRateLimiter


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
