from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel

from rifthub_backend.voting import remove_comment_vote, vote_on_comment

from rifthub_api.dependencies import AppSettings, DbSession, RequiredCurrentSession, validate_session_csrf
from rifthub_api.schemas import CommentVoteResponse

router = APIRouter(prefix="/comments", tags=["comments"])


class VoteRequest(BaseModel):
    vote_value: Literal[1, -1]


@router.post("/{comment_id}/vote", response_model=CommentVoteResponse)
async def create_comment_vote(
    comment_id: UUID,
    payload: VoteRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> CommentVoteResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return CommentVoteResponse.model_validate(
        {
            "comment": await vote_on_comment(
                db=db,
                user=current_session.user,
                comment_id=comment_id,
                vote_value=payload.vote_value,
            )
        }
    )


@router.delete("/{comment_id}/vote", response_model=CommentVoteResponse)
async def delete_comment_vote(
    comment_id: UUID,
    request: Request,
    db: DbSession,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> CommentVoteResponse:
    validate_session_csrf(
        request=request,
        settings=settings,
        current_session=current_session,
    )
    return CommentVoteResponse.model_validate(
        {
            "comment": await remove_comment_vote(
                db=db,
                user=current_session.user,
                comment_id=comment_id,
            )
        }
    )
