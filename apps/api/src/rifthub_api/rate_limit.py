from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import asyncio
import time

from .errors import ApiError


@dataclass
class _WindowState:
    hits: deque[float] = field(default_factory=deque)


class InMemoryRateLimiter:
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


rate_limiter = InMemoryRateLimiter()
