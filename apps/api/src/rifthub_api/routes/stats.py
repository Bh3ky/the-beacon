from __future__ import annotations

from fastapi import APIRouter

from rifthub_backend.summary import get_platform_summary

from rifthub_api.dependencies import DbSession
from rifthub_api.schemas import PlatformSummaryPayload

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=PlatformSummaryPayload)
async def platform_summary(db: DbSession) -> PlatformSummaryPayload:
    return PlatformSummaryPayload.model_validate(await get_platform_summary(db))
