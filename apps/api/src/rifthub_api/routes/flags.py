from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from rifthub_backend.db.types import FlagReason, FlagTargetType
from rifthub_backend.flags import CreateFlagInput, create_flag

from rifthub_api.dependencies import AppSettings, DbSession, RequiredCurrentSession, validate_session_csrf
from rifthub_api.schemas import FlagResponse

router = APIRouter(prefix="/flags", tags=["flags"])


class CreateFlagRequest(BaseModel):
    target_type: FlagTargetType
    target_id: UUID
    reason_code: FlagReason
    notes: str | None = None


@router.post("", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
async def create_flag_route(
    payload: CreateFlagRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> FlagResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    flag = await create_flag(
        db=db,
        reporter=current_session.user,
        payload=CreateFlagInput(
            target_type=payload.target_type,
            target_id=payload.target_id,
            reason_code=payload.reason_code,
            notes=payload.notes,
        ),
    )
    return FlagResponse.model_validate({"flag": flag})
