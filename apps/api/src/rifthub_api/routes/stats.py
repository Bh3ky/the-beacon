from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter
from rifthub_backend.summary import get_platform_summary

from rifthub_api.dependencies import DbSession
from rifthub_api.schemas import PlatformSummaryPayload

router = APIRouter(prefix="/stats", tags=["stats"])

CACHE_SECONDS = 60


class _SummaryCache:
    def __init__(self) -> None:
        self.value: PlatformSummaryPayload | None = None
        self.stored_at = 0.0
        self.lock = asyncio.Lock()

    def fresh_value(self) -> PlatformSummaryPayload | None:
        if self.value is not None and time.monotonic() - self.stored_at < CACHE_SECONDS:
            return self.value
        return None


_cache = _SummaryCache()


@router.get("/summary", response_model=PlatformSummaryPayload)
async def platform_summary(db: DbSession) -> PlatformSummaryPayload:
    cached = _cache.fresh_value()
    if cached is not None:
        return cached

    async with _cache.lock:
        cached = _cache.fresh_value()
        if cached is not None:
            return cached

        _cache.value = PlatformSummaryPayload.model_validate(await get_platform_summary(db))
        _cache.stored_at = time.monotonic()
        return _cache.value
