from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.db.types import (
    CommentStatus,
    FlagStatus,
    FlagTargetType,
    IngestionStatus,
    ModerationActionType,
    ModerationTargetType,
    PostStatus,
    SourceStatus,
    UserStatus,
)
from rifthub_backend.models.comment import Comment
from rifthub_backend.models.flag import Flag
from rifthub_backend.models.ingestion import IngestionItem
from rifthub_backend.models.moderation import ModerationAction
from rifthub_backend.models.post import Post
from rifthub_backend.models.source import Source
from rifthub_backend.models.user import User
from rifthub_backend.ingestion_publication import (
    publish_ingestion_item,
    resolve_or_create_ingestion_system_user,
)


@dataclass(slots=True)
class ModerationError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


@dataclass(frozen=True, slots=True)
class ModeratorSummary:
    id: UUID
    username: str


@dataclass(frozen=True, slots=True)
class ModerationTargetSummary:
    id: UUID
    target_type: FlagTargetType
    title: str | None
    excerpt: str | None
    username: str | None
    status: str


@dataclass(frozen=True, slots=True)
class FlagQueueItem:
    flag: Flag
    reporter: ModeratorSummary
    target: ModerationTargetSummary


@dataclass(frozen=True, slots=True)
class ModerationResult:
    action: ModerationAction
    flag: Flag | None


@dataclass(frozen=True, slots=True)
class IngestionSourceSummary:
    id: UUID
    name: str
    source_type: str
    status: str
    auto_publish: bool


@dataclass(frozen=True, slots=True)
class IngestionReviewItemSummary:
    id: UUID
    title: str
    url: str
    ingestion_status: str
    detected_category: str | None
    published_at_external: datetime | None
    discovered_at: datetime
    processing_notes: str | None
    source: IngestionSourceSummary
    linked_post_id: UUID | None
    dedupe_match_post_id: UUID | None


@dataclass(frozen=True, slots=True)
class SourceHealthSummary:
    id: UUID
    name: str
    source_type: str
    status: str
    auto_publish: bool
    poll_interval_minutes: int
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None


@dataclass(frozen=True, slots=True)
class ModerationActionInput:
    reason: str | None = None
    flag_id: UUID | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _normalize_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    normalized = reason.strip()
    return normalized or None


def _reporter_summary(user: User) -> ModeratorSummary:
    return ModeratorSummary(id=user.id, username=user.username)


def _comment_excerpt(body_markdown: str, *, limit: int = 160) -> str:
    excerpt = " ".join(body_markdown.split())
    if len(excerpt) <= limit:
        return excerpt
    return f"{excerpt[: limit - 1].rstrip()}…"


def _target_summary_from_post(post: Post) -> ModerationTargetSummary:
    return ModerationTargetSummary(
        id=post.id,
        target_type=FlagTargetType.POST,
        title=post.title,
        excerpt=post.body_markdown,
        username=post.author.username,
        status=post.status.value,
    )


def _target_summary_from_comment(comment: Comment) -> ModerationTargetSummary:
    return ModerationTargetSummary(
        id=comment.id,
        target_type=FlagTargetType.COMMENT,
        title=None,
        excerpt=_comment_excerpt(comment.body_markdown),
        username=comment.author.username,
        status=comment.status.value,
    )


def _target_summary_from_user(user: User) -> ModerationTargetSummary:
    return ModerationTargetSummary(
        id=user.id,
        target_type=FlagTargetType.USER,
        title=None,
        excerpt=user.bio,
        username=user.username,
        status=user.status.value,
    )


async def _load_open_flag_for_review(*, db: AsyncSession, flag_id: UUID) -> Flag:
    flag = await db.scalar(
        select(Flag).options(joinedload(Flag.reporter)).where(Flag.id == flag_id, Flag.status == FlagStatus.OPEN)
    )
    if flag is None:
        raise ModerationError(404, "flag_not_found", "The requested open flag does not exist.")
    return flag


async def _resolve_related_flag(
    *,
    db: AsyncSession,
    flag_id: UUID | None,
    target_type: FlagTargetType,
    target_id: UUID,
) -> Flag | None:
    if flag_id is None:
        return None

    flag = await _load_open_flag_for_review(db=db, flag_id=flag_id)
    if flag.target_type != target_type or flag.target_id != target_id:
        raise ModerationError(
            400,
            "flag_target_mismatch",
            "The referenced flag does not match the moderation target.",
        )
    return flag


def _mark_flag_reviewed(*, flag: Flag, moderator: User, status: FlagStatus) -> None:
    flag.status = status
    flag.reviewed_by_user_id = moderator.id
    flag.reviewed_at = _utcnow()


async def _record_action(
    *,
    db: AsyncSession,
    moderator: User,
    target_type: ModerationTargetType,
    target_id: UUID,
    action_type: ModerationActionType,
    reason: str | None,
    metadata_json: dict[str, object] | None,
) -> ModerationAction:
    action = ModerationAction(
        moderator_id=moderator.id,
        target_type=target_type,
        target_id=target_id,
        action_type=action_type,
        reason=reason,
        metadata_json=metadata_json,
    )
    db.add(action)
    await db.flush()
    return action


async def _load_post_for_moderation(*, db: AsyncSession, post_id: UUID) -> Post:
    post = await db.scalar(select(Post).options(joinedload(Post.author)).where(Post.id == post_id))
    if post is None:
        raise ModerationError(404, "post_not_found", "The requested post does not exist.")
    return post


async def _load_comment_for_moderation(*, db: AsyncSession, comment_id: UUID) -> Comment:
    comment = await db.scalar(
        select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment_id)
    )
    if comment is None:
        raise ModerationError(404, "comment_not_found", "The requested comment does not exist.")
    return comment


async def _load_user_for_moderation(*, db: AsyncSession, user_id: UUID) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise ModerationError(404, "user_not_found", "The requested user does not exist.")
    return user


async def _load_ingestion_item_for_moderation(*, db: AsyncSession, item_id: UUID) -> IngestionItem:
    item = await db.scalar(
        select(IngestionItem)
        .options(joinedload(IngestionItem.source))
        .where(IngestionItem.id == item_id)
    )
    if item is None:
        raise ModerationError(404, "ingestion_item_not_found", "The requested ingestion item does not exist.")
    return item


def _ingestion_source_summary(source: Source) -> IngestionSourceSummary:
    return IngestionSourceSummary(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        status=source.status.value,
        auto_publish=source.auto_publish,
    )


def _ingestion_review_summary(item: IngestionItem) -> IngestionReviewItemSummary:
    return IngestionReviewItemSummary(
        id=item.id,
        title=item.title,
        url=item.url,
        ingestion_status=item.ingestion_status.value,
        detected_category=item.detected_category.value if item.detected_category is not None else None,
        published_at_external=item.published_at_external,
        discovered_at=item.discovered_at,
        processing_notes=item.processing_notes,
        source=_ingestion_source_summary(item.source),
        linked_post_id=item.linked_post_id,
        dedupe_match_post_id=item.dedupe_match_post_id,
    )


async def list_open_flags(*, db: AsyncSession, limit: int = 50) -> list[FlagQueueItem]:
    rows = list(
        (
            await db.scalars(
                select(Flag)
                .options(joinedload(Flag.reporter))
                .where(Flag.status == FlagStatus.OPEN)
                .order_by(Flag.created_at.asc(), Flag.id.asc())
                .limit(limit)
            )
        ).all()
    )
    if not rows:
        return []

    post_ids = [flag.target_id for flag in rows if flag.target_type == FlagTargetType.POST]
    comment_ids = [flag.target_id for flag in rows if flag.target_type == FlagTargetType.COMMENT]
    user_ids = [flag.target_id for flag in rows if flag.target_type == FlagTargetType.USER]

    posts = {
        post.id: post
        for post in (
            await db.scalars(select(Post).options(joinedload(Post.author)).where(Post.id.in_(post_ids)))
        ).all()
    }
    comments = {
        comment.id: comment
        for comment in (
            await db.scalars(
                select(Comment).options(joinedload(Comment.author)).where(Comment.id.in_(comment_ids))
            )
        ).all()
    }
    users = {
        user.id: user
        for user in (await db.scalars(select(User).where(User.id.in_(user_ids)))).all()
    }

    items: list[FlagQueueItem] = []
    for flag in rows:
        if flag.target_type == FlagTargetType.POST:
            target = posts.get(flag.target_id)
            if target is None:
                continue
            target_summary = _target_summary_from_post(target)
        elif flag.target_type == FlagTargetType.COMMENT:
            target = comments.get(flag.target_id)
            if target is None:
                continue
            target_summary = _target_summary_from_comment(target)
        else:
            target = users.get(flag.target_id)
            if target is None:
                continue
            target_summary = _target_summary_from_user(target)

        items.append(
            FlagQueueItem(
                flag=flag,
                reporter=_reporter_summary(flag.reporter),
                target=target_summary,
            )
        )

    return items


async def list_ingestion_review_items(*, db: AsyncSession, limit: int = 50) -> list[IngestionReviewItemSummary]:
    items = list(
        (
            await db.scalars(
                select(IngestionItem)
                .options(joinedload(IngestionItem.source))
                .where(IngestionItem.ingestion_status == IngestionStatus.AWAITING_REVIEW)
                .order_by(IngestionItem.discovered_at.asc(), IngestionItem.id.asc())
                .limit(limit)
            )
        ).all()
    )
    return [_ingestion_review_summary(item) for item in items]


async def list_source_health(
    *,
    db: AsyncSession,
    limit: int = 20,
    failures_only: bool = True,
) -> list[SourceHealthSummary]:
    statement = select(Source).order_by(Source.last_error_at.desc().nullslast(), Source.id.asc()).limit(limit)
    if failures_only:
        statement = statement.where(
            Source.status == SourceStatus.ACTIVE,
            Source.last_error_at.is_not(None),
        )

    sources = list((await db.scalars(statement)).all())
    return [
        SourceHealthSummary(
            id=source.id,
            name=source.name,
            source_type=source.source_type.value,
            status=source.status.value,
            auto_publish=source.auto_publish,
            poll_interval_minutes=source.poll_interval_minutes,
            last_checked_at=source.last_checked_at,
            last_success_at=source.last_success_at,
            last_error_at=source.last_error_at,
            last_error_message=source.last_error_message,
        )
        for source in sources
    ]


async def dismiss_flag(
    *,
    db: AsyncSession,
    moderator: User,
    flag_id: UUID,
) -> Flag:
    flag = await _load_open_flag_for_review(db=db, flag_id=flag_id)
    _mark_flag_reviewed(flag=flag, moderator=moderator, status=FlagStatus.DISMISSED)
    await db.commit()
    await db.refresh(flag)
    return flag


async def remove_post(
    *,
    db: AsyncSession,
    moderator: User,
    post_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    post = await _load_post_for_moderation(db=db, post_id=post_id)
    if post.status == PostStatus.REMOVED:
        raise ModerationError(409, "post_already_removed", "The post is already removed.")

    flag = await _resolve_related_flag(
        db=db,
        flag_id=payload.flag_id,
        target_type=FlagTargetType.POST,
        target_id=post.id,
    )

    previous_status = post.status.value
    post.status = PostStatus.REMOVED
    if flag is not None:
        _mark_flag_reviewed(flag=flag, moderator=moderator, status=FlagStatus.RESOLVED)

    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.POST,
        target_id=post.id,
        action_type=ModerationActionType.REMOVE,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "flag_id": str(flag.id) if flag is not None else None,
            "previous_status": previous_status,
            "new_status": PostStatus.REMOVED.value,
        },
    )
    await db.commit()
    await db.refresh(action)
    if flag is not None:
        await db.refresh(flag)
    return ModerationResult(action=action, flag=flag)


async def remove_comment(
    *,
    db: AsyncSession,
    moderator: User,
    comment_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    comment = await _load_comment_for_moderation(db=db, comment_id=comment_id)
    if comment.status == CommentStatus.REMOVED:
        raise ModerationError(409, "comment_already_removed", "The comment is already removed.")

    flag = await _resolve_related_flag(
        db=db,
        flag_id=payload.flag_id,
        target_type=FlagTargetType.COMMENT,
        target_id=comment.id,
    )

    previous_status = comment.status.value
    comment.status = CommentStatus.REMOVED
    if flag is not None:
        _mark_flag_reviewed(flag=flag, moderator=moderator, status=FlagStatus.RESOLVED)

    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.COMMENT,
        target_id=comment.id,
        action_type=ModerationActionType.REMOVE,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "flag_id": str(flag.id) if flag is not None else None,
            "previous_status": previous_status,
            "new_status": CommentStatus.REMOVED.value,
        },
    )
    await db.commit()
    await db.refresh(action)
    if flag is not None:
        await db.refresh(flag)
    return ModerationResult(action=action, flag=flag)


async def suspend_user(
    *,
    db: AsyncSession,
    moderator: User,
    user_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    user = await _load_user_for_moderation(db=db, user_id=user_id)
    if user.status == UserStatus.SUSPENDED:
        raise ModerationError(409, "user_already_suspended", "The user is already suspended.")
    if user.status == UserStatus.BANNED:
        raise ModerationError(409, "user_already_banned", "The user is already banned.")

    flag = await _resolve_related_flag(
        db=db,
        flag_id=payload.flag_id,
        target_type=FlagTargetType.USER,
        target_id=user.id,
    )

    previous_status = user.status.value
    user.status = UserStatus.SUSPENDED
    if flag is not None:
        _mark_flag_reviewed(flag=flag, moderator=moderator, status=FlagStatus.RESOLVED)

    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.USER,
        target_id=user.id,
        action_type=ModerationActionType.SUSPEND_USER,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "flag_id": str(flag.id) if flag is not None else None,
            "previous_status": previous_status,
            "new_status": UserStatus.SUSPENDED.value,
        },
    )
    await db.commit()
    await db.refresh(action)
    if flag is not None:
        await db.refresh(flag)
    return ModerationResult(action=action, flag=flag)


async def ban_user(
    *,
    db: AsyncSession,
    moderator: User,
    user_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    user = await _load_user_for_moderation(db=db, user_id=user_id)
    if user.status == UserStatus.BANNED:
        raise ModerationError(409, "user_already_banned", "The user is already banned.")

    flag = await _resolve_related_flag(
        db=db,
        flag_id=payload.flag_id,
        target_type=FlagTargetType.USER,
        target_id=user.id,
    )

    previous_status = user.status.value
    user.status = UserStatus.BANNED
    if flag is not None:
        _mark_flag_reviewed(flag=flag, moderator=moderator, status=FlagStatus.RESOLVED)

    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.USER,
        target_id=user.id,
        action_type=ModerationActionType.BAN_USER,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "flag_id": str(flag.id) if flag is not None else None,
            "previous_status": previous_status,
            "new_status": UserStatus.BANNED.value,
        },
    )
    await db.commit()
    await db.refresh(action)
    if flag is not None:
        await db.refresh(flag)
    return ModerationResult(action=action, flag=flag)


async def approve_ingestion_item(
    *,
    db: AsyncSession,
    moderator: User,
    item_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    item = await _load_ingestion_item_for_moderation(db=db, item_id=item_id)
    if item.ingestion_status != IngestionStatus.AWAITING_REVIEW:
        raise ModerationError(
            409,
            "ingestion_item_not_awaiting_review",
            "The ingestion item is not awaiting review.",
        )

    system_user = await resolve_or_create_ingestion_system_user(db=db)
    previous_status = item.ingestion_status.value
    publish_result = await publish_ingestion_item(
        db=db,
        source=item.source,
        item=item,
        author=system_user,
    )
    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.INGESTION_ITEM,
        target_id=item.id,
        action_type=ModerationActionType.APPROVE_INGESTION,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "source_id": str(item.source_id),
            "previous_status": previous_status,
            "new_status": item.ingestion_status.value,
            "publish_result": publish_result,
            "linked_post_id": str(item.linked_post_id) if item.linked_post_id is not None else None,
            "dedupe_match_post_id": (
                str(item.dedupe_match_post_id) if item.dedupe_match_post_id is not None else None
            ),
        },
    )
    await db.commit()
    await db.refresh(action)
    return ModerationResult(action=action, flag=None)


async def reject_ingestion_item(
    *,
    db: AsyncSession,
    moderator: User,
    item_id: UUID,
    payload: ModerationActionInput,
) -> ModerationResult:
    item = await _load_ingestion_item_for_moderation(db=db, item_id=item_id)
    if item.ingestion_status != IngestionStatus.AWAITING_REVIEW:
        raise ModerationError(
            409,
            "ingestion_item_not_awaiting_review",
            "The ingestion item is not awaiting review.",
        )

    previous_status = item.ingestion_status.value
    item.ingestion_status = IngestionStatus.REJECTED
    item.processing_notes = "Rejected during ingestion review."
    action = await _record_action(
        db=db,
        moderator=moderator,
        target_type=ModerationTargetType.INGESTION_ITEM,
        target_id=item.id,
        action_type=ModerationActionType.REJECT_INGESTION,
        reason=_normalize_reason(payload.reason),
        metadata_json={
            "source_id": str(item.source_id),
            "previous_status": previous_status,
            "new_status": item.ingestion_status.value,
        },
    )
    await db.commit()
    await db.refresh(action)
    return ModerationResult(action=action, flag=None)
