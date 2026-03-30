from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from rifthub_backend.moderation import (
    ModerationActionInput,
    approve_ingestion_item,
    ban_user,
    dismiss_flag,
    list_open_flags,
    list_ingestion_review_items,
    list_source_health,
    reject_ingestion_item,
    remove_comment,
    remove_post,
    suspend_user,
)

from rifthub_api.dependencies import (
    AppSettings,
    DbSession,
    RequireAdminSession,
    RequireModeratorSession,
    validate_session_csrf,
)
from rifthub_api.schemas import (
    FlagQueueResponse,
    FlagResponse,
    IngestionReviewQueueResponse,
    ModerationActionResponse,
    SourceHealthResponse,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


class ModerationActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)
    flag_id: UUID | None = None


@router.get("/flags", response_model=FlagQueueResponse)
async def list_open_flags_route(
    db: DbSession,
    current_session: RequireModeratorSession,
    limit: int = Query(default=50, ge=1, le=100),
) -> FlagQueueResponse:
    del current_session
    items = await list_open_flags(db=db, limit=limit)
    return FlagQueueResponse.model_validate({"items": items})


@router.get("/ingestion/items", response_model=IngestionReviewQueueResponse)
async def list_ingestion_review_items_route(
    db: DbSession,
    current_session: RequireModeratorSession,
    limit: int = Query(default=50, ge=1, le=100),
) -> IngestionReviewQueueResponse:
    del current_session
    items = await list_ingestion_review_items(db=db, limit=limit)
    return IngestionReviewQueueResponse.model_validate({"items": items})


@router.get("/ingestion/sources", response_model=SourceHealthResponse)
async def list_source_health_route(
    db: DbSession,
    current_session: RequireModeratorSession,
    limit: int = Query(default=20, ge=1, le=100),
    failures_only: bool = Query(default=True),
) -> SourceHealthResponse:
    del current_session
    items = await list_source_health(db=db, limit=limit, failures_only=failures_only)
    return SourceHealthResponse.model_validate({"items": items})


@router.post("/flags/{flag_id}/dismiss", response_model=FlagResponse)
async def dismiss_flag_route(
    flag_id: UUID,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireModeratorSession,
) -> FlagResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    flag = await dismiss_flag(
        db=db,
        moderator=current_session.user,
        flag_id=flag_id,
    )
    return FlagResponse.model_validate({"flag": flag})


@router.post("/posts/{post_id}/remove", response_model=ModerationActionResponse)
async def remove_post_route(
    post_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireModeratorSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await remove_post(
        db=db,
        moderator=current_session.user,
        post_id=post_id,
        payload=ModerationActionInput(reason=payload.reason, flag_id=payload.flag_id),
    )
    return ModerationActionResponse.model_validate(result)


@router.post("/comments/{comment_id}/remove", response_model=ModerationActionResponse)
async def remove_comment_route(
    comment_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireModeratorSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await remove_comment(
        db=db,
        moderator=current_session.user,
        comment_id=comment_id,
        payload=ModerationActionInput(reason=payload.reason, flag_id=payload.flag_id),
    )
    return ModerationActionResponse.model_validate(result)


@router.post("/users/{user_id}/suspend", response_model=ModerationActionResponse)
async def suspend_user_route(
    user_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireModeratorSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await suspend_user(
        db=db,
        moderator=current_session.user,
        user_id=user_id,
        payload=ModerationActionInput(reason=payload.reason, flag_id=payload.flag_id),
    )
    return ModerationActionResponse.model_validate(result)


@router.post("/users/{user_id}/ban", response_model=ModerationActionResponse)
async def ban_user_route(
    user_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireAdminSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await ban_user(
        db=db,
        moderator=current_session.user,
        user_id=user_id,
        payload=ModerationActionInput(reason=payload.reason, flag_id=payload.flag_id),
    )
    return ModerationActionResponse.model_validate(result)


@router.post("/ingestion/items/{item_id}/approve", response_model=ModerationActionResponse)
async def approve_ingestion_item_route(
    item_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireAdminSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await approve_ingestion_item(
        db=db,
        moderator=current_session.user,
        item_id=item_id,
        payload=ModerationActionInput(reason=payload.reason),
    )
    return ModerationActionResponse.model_validate(result)


@router.post("/ingestion/items/{item_id}/reject", response_model=ModerationActionResponse)
async def reject_ingestion_item_route(
    item_id: UUID,
    payload: ModerationActionRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequireAdminSession,
) -> ModerationActionResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    result = await reject_ingestion_item(
        db=db,
        moderator=current_session.user,
        item_id=item_id,
        payload=ModerationActionInput(reason=payload.reason),
    )
    return ModerationActionResponse.model_validate(result)
