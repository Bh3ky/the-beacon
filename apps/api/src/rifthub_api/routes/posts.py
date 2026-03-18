from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request, status
from pydantic import BaseModel

from rifthub_backend.creation import (
    CreateCommentInput,
    CreatePostInput,
    create_comment,
    create_post,
)
from rifthub_backend.db.types import Category, PostType, UserRole
from rifthub_backend.reads import CommentSort, get_post_comments, get_post_detail
from rifthub_backend.voting import remove_post_vote, vote_on_post

from rifthub_api.dependencies import AppSettings, CurrentSessionDep, DbSession, RequiredCurrentSession, validate_session_csrf
from rifthub_api.schemas import CommentListResponse, CommentResponse, PostResponse, PostVoteResponse

router = APIRouter(prefix="/posts", tags=["posts"])


class CreatePostRequest(BaseModel):
    post_type: PostType
    category: Category
    title: str
    url: str | None = None
    body_markdown: str | None = None
    job_expires_at: datetime | None = None


class CreateCommentRequest(BaseModel):
    body_markdown: str
    parent_comment_id: UUID | None = None


class VoteRequest(BaseModel):
    vote_value: Literal[1, -1]


def _viewer_context(current_session: CurrentSessionDep) -> tuple[UUID | None, UserRole | None]:
    if current_session is None:
        return None, None
    return current_session.user.id, current_session.user.role


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_route(
    payload: CreatePostRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> PostResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return PostResponse.model_validate(
        {
            "post": await create_post(
                db=db,
                author=current_session.user,
                payload=CreatePostInput(
                    post_type=payload.post_type,
                    category=payload.category,
                    title=payload.title,
                    url=payload.url,
                    body_markdown=payload.body_markdown,
                    job_expires_at=payload.job_expires_at,
                ),
            )
        }
    )


@router.get("/{post_id}", response_model=PostResponse)
async def post_detail(
    post_id: UUID,
    db: DbSession,
    current_session: CurrentSessionDep,
) -> PostResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return PostResponse.model_validate(
        {
            "post": await get_post_detail(
                db=db,
                post_id=post_id,
                viewer_user_id=viewer_user_id,
                viewer_role=viewer_role,
            )
        }
    )


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def post_comments(
    post_id: UUID,
    db: DbSession,
    current_session: CurrentSessionDep,
    sort: CommentSort = Query(default="top"),
) -> CommentListResponse:
    viewer_user_id, viewer_role = _viewer_context(current_session)
    return CommentListResponse.model_validate(
        await get_post_comments(
            db=db,
            post_id=post_id,
            sort=sort,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
        )
    )


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_post_comment(
    post_id: UUID,
    payload: CreateCommentRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> CommentResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return CommentResponse.model_validate(
        {
            "comment": await create_comment(
                db=db,
                author=current_session.user,
                post_id=post_id,
                payload=CreateCommentInput(
                    body_markdown=payload.body_markdown,
                    parent_comment_id=payload.parent_comment_id,
                ),
            )
        }
    )


@router.post("/{post_id}/vote", response_model=PostVoteResponse)
async def create_post_vote(
    post_id: UUID,
    payload: VoteRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> PostVoteResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return PostVoteResponse.model_validate(
        {
            "post": await vote_on_post(
                db=db,
                user=current_session.user,
                post_id=post_id,
                vote_value=payload.vote_value,
            )
        }
    )


@router.delete("/{post_id}/vote", response_model=PostVoteResponse)
async def delete_post_vote(
    post_id: UUID,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> PostVoteResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return PostVoteResponse.model_validate(
        {
            "post": await remove_post_vote(
                db=db,
                user=current_session.user,
                post_id=post_id,
            )
        }
    )
