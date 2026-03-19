from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from rifthub_backend.db.types import UserRole
from rifthub_backend.reads import get_ask_feed, get_jobs_feed, get_new_feed, get_show_feed, get_top_feed

from rifthub_api.dependencies import CurrentSessionDep, DbSession
from rifthub_api.schemas import FeedResponse

router = APIRouter(prefix="/feeds", tags=["feeds"])


def _viewer_context(current_session: CurrentSessionDep) -> tuple[UUID | None, UserRole | None]:
    if current_session is None:
        return None, None
    return current_session.user.id, current_session.user.role


@router.get("/top", response_model=FeedResponse)
async def top_feed(
    db: DbSession,
    current_session: CurrentSessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
) -> FeedResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return FeedResponse.model_validate(
        await get_top_feed(
            db=db,
            limit=limit,
            cursor=cursor,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )


@router.get("/new", response_model=FeedResponse)
async def new_feed(
    db: DbSession,
    current_session: CurrentSessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
) -> FeedResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return FeedResponse.model_validate(
        await get_new_feed(
            db=db,
            limit=limit,
            cursor=cursor,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )


@router.get("/jobs", response_model=FeedResponse)
async def jobs_feed(
    db: DbSession,
    current_session: CurrentSessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
) -> FeedResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return FeedResponse.model_validate(
        await get_jobs_feed(
            db=db,
            limit=limit,
            cursor=cursor,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )


@router.get("/ask", response_model=FeedResponse)
async def ask_feed(
    db: DbSession,
    current_session: CurrentSessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
) -> FeedResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return FeedResponse.model_validate(
        await get_ask_feed(
            db=db,
            limit=limit,
            cursor=cursor,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )


@router.get("/show", response_model=FeedResponse)
async def show_feed(
    db: DbSession,
    current_session: CurrentSessionDep,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
) -> FeedResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return FeedResponse.model_validate(
        await get_show_feed(
            db=db,
            limit=limit,
            cursor=cursor,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )
