from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import (
    CommentStatus,
    FlagReason,
    FlagStatus,
    FlagTargetType,
    PostStatus,
    UserStatus,
)
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.flag import Flag
from rifthub_backend.models.post import Post
from rifthub_backend.models.user import User
from rifthub_backend.write_access import user_has_restricted_write_access

OPEN_FLAG_CONSTRAINT_NAME = "uq_flags_open_reporter_target_reason"


@dataclass(slots=True)
class FlaggingError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


@dataclass(frozen=True, slots=True)
class CreateFlagInput:
    target_type: FlagTargetType
    target_id: UUID
    reason_code: FlagReason
    notes: str | None


def _require_active_reporter(*, user: User) -> None:
    if user_has_restricted_write_access(status=user.status):
        raise FlaggingError(403, "forbidden", "Your account cannot perform this action.")


def _is_duplicate_open_flag_error(exc: IntegrityError) -> bool:
    constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    return constraint_name == OPEN_FLAG_CONSTRAINT_NAME


async def _ensure_target_exists(*, db: AsyncSession, target_type: FlagTargetType, target_id: UUID) -> None:
    if target_type == FlagTargetType.POST:
        target = await db.scalar(
            select(Post.id).where(Post.id == target_id, Post.status == PostStatus.ACTIVE)
        )
        if target is None:
            raise FlaggingError(404, "post_not_found", "The requested post does not exist.")
        return

    if target_type == FlagTargetType.COMMENT:
        target = await db.scalar(
            select(Comment.id).where(
                Comment.id == target_id,
                Comment.status == CommentStatus.ACTIVE,
            )
        )
        if target is None:
            raise FlaggingError(404, "comment_not_found", "The requested comment does not exist.")
        return

    target = await db.scalar(
        select(User.id).where(User.id == target_id, User.status == UserStatus.ACTIVE)
    )
    if target is None:
        raise FlaggingError(404, "user_not_found", "The requested user does not exist.")


async def create_flag(
    *,
    db: AsyncSession,
    reporter: User,
    payload: CreateFlagInput,
) -> Flag:
    _require_active_reporter(user=reporter)
    await _ensure_target_exists(
        db=db,
        target_type=payload.target_type,
        target_id=payload.target_id,
    )

    notes = payload.notes.strip() if payload.notes else None
    if notes == "":
        notes = None

    flag = Flag(
        target_type=payload.target_type,
        target_id=payload.target_id,
        reporter_id=reporter.id,
        reason_code=payload.reason_code,
        notes=notes,
        status=FlagStatus.OPEN,
    )
    db.add(flag)

    try:
        await db.flush()
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if _is_duplicate_open_flag_error(exc):
            raise FlaggingError(
                409,
                "duplicate_open_flag",
                "You have already reported this for the same reason.",
            ) from exc
        raise

    return flag
