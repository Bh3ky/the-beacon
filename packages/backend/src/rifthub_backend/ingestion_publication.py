from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.auth.security import canonicalize_email, canonicalize_username
from rifthub_backend.config import get_settings
from rifthub_backend.creation import ACTIVE_LINK_URL_CONSTRAINT_NAME, slugify_title
from rifthub_backend.db.types import Category, IngestionStatus, PostStatus, PostType, UserRole, UserStatus
from rifthub_backend.domains import resolve_or_create_domain
from rifthub_backend.ingestion_normalization import hostname_from_normalized_url
from rifthub_backend.models.ingestion import IngestionItem
from rifthub_backend.models.post import Post
from rifthub_backend.models.source import Source
from rifthub_backend.models.user import User
from rifthub_backend.voting import compute_post_rank_score

INGESTION_SYSTEM_DISABLED_PASSWORD_HASH = "service-account-disabled"
_DEFAULT_INGESTION_CATEGORY = Category.ECOSYSTEM
_KEYWORD_CATEGORY_RULES: tuple[tuple[Category, tuple[str, ...]], ...] = (
    (Category.JOBS, ("hiring", "we're hiring", "job opening", "job", "careers")),
    (Category.FUNDING, ("raises", "raised", "funding", "seed round", "series a", "series b")),
    (Category.POLICY, ("policy", "regulation", "regulatory", "government", "tax", "licence")),
    (Category.ENGINEERING, ("engineering", "open source", "developer", "infrastructure", "sdk", "api")),
    (Category.LAUNCH, ("launch", "launches", "launched", "introduces", "ships", "rolls out")),
)


class PersistedEntryRef(Protocol):
    external_id: str | None
    url: str


@dataclass(frozen=True, slots=True)
class ProcessIngestionEntriesResult:
    processed_item_count: int
    published_item_count: int
    awaiting_review_item_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


def classify_ingestion_category(*, source: Source, title: str) -> Category:
    lowered_title = title.strip().lower()
    inherited_category = source.default_category
    if inherited_category not in {None, Category.ECOSYSTEM}:
        return inherited_category

    for category, keywords in _KEYWORD_CATEGORY_RULES:
        if any(keyword in lowered_title for keyword in keywords):
            return category

    return inherited_category or _DEFAULT_INGESTION_CATEGORY


async def resolve_or_create_ingestion_system_user(*, db: AsyncSession) -> User:
    settings = get_settings()
    username = canonicalize_username(settings.ingestion_system_username)
    email = canonicalize_email(settings.ingestion_system_email)

    user = await db.scalar(select(User).where(User.username == username))
    if user is not None:
        return user

    now = _utcnow()
    inserted_user_id = await db.scalar(
        pg_insert(User)
        .values(
            username=username,
            email=email,
            password_hash=INGESTION_SYSTEM_DISABLED_PASSWORD_HASH,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            last_active_at=now,
        )
        .on_conflict_do_nothing(index_elements=[User.username])
        .returning(User.id)
    )
    if inserted_user_id is None:
        user = await db.scalar(select(User).where(User.username == username))
        if user is None:  # pragma: no cover - indicates conflicting email config
            raise RuntimeError("Configured ingestion system user could not be created.")
    else:
        user = await db.scalar(select(User).where(User.id == inserted_user_id))
        if user is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Inserted ingestion system user could not be reloaded.")
    return user


async def _load_ingestion_item_for_entry(
    *,
    db: AsyncSession,
    source_id,
    entry: PersistedEntryRef,
) -> IngestionItem | None:
    if entry.external_id is not None:
        statement = select(IngestionItem).where(
            IngestionItem.source_id == source_id,
            IngestionItem.external_id == entry.external_id,
        )
    else:
        statement = select(IngestionItem).where(
            IngestionItem.source_id == source_id,
            IngestionItem.external_id.is_(None),
            IngestionItem.url_normalized == entry.url,
        )
    return await db.scalar(statement)


def _mark_item_duplicate(*, item: IngestionItem, matched_post: Post) -> None:
    item.ingestion_status = IngestionStatus.DUPLICATE
    item.linked_post_id = None
    item.dedupe_match_post_id = matched_post.id
    item.processing_notes = "Matched existing active post during publish."


async def publish_ingestion_item(
    *,
    db: AsyncSession,
    source: Source,
    item: IngestionItem,
    author: User,
    now: datetime | None = None,
) -> str:
    current_time = _utcnow() if now is None else now

    existing_post = await db.scalar(
        select(Post).where(
            Post.status == PostStatus.ACTIVE,
            Post.url_normalized == item.url_normalized,
        )
    )
    if existing_post is not None:
        _mark_item_duplicate(item=item, matched_post=existing_post)
        return "duplicate"

    if item.url_normalized is None:
        item.ingestion_status = IngestionStatus.FAILED
        item.processing_notes = "Normalized URL is required before publication."
        return "failed"

    domain = await resolve_or_create_domain(
        db=db,
        hostname=hostname_from_normalized_url(item.url_normalized),
    )
    category = item.detected_category or classify_ingestion_category(source=source, title=item.title)
    inserted_post_id = await db.scalar(
        pg_insert(Post)
        .values(
            author_id=author.id,
            post_type=PostType.LINK,
            category=category,
            title=item.title,
            slug=slugify_title(item.title),
            url=item.url,
            url_normalized=item.url_normalized,
            domain_id=domain.id,
            status=PostStatus.ACTIVE,
            is_ingested=True,
            ingested_from_source_id=source.id,
            rank_score=compute_post_rank_score(
                score=0,
                submitted_at=current_time,
                comment_count=0,
                category=category,
                domain_trust_score=domain.trust_score,
                now=current_time,
            ),
            submitted_at=current_time,
        )
        .on_conflict_do_nothing(constraint=ACTIVE_LINK_URL_CONSTRAINT_NAME)
        .returning(Post.id)
    )
    if inserted_post_id is None:
        existing_post = await db.scalar(
            select(Post).where(
                Post.status == PostStatus.ACTIVE,
                Post.url_normalized == item.url_normalized,
            )
        )
        if existing_post is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Expected an active post after ingestion publish conflict.")
        _mark_item_duplicate(item=item, matched_post=existing_post)
        return "duplicate"

    item.ingestion_status = IngestionStatus.PUBLISHED
    item.detected_category = category
    item.linked_post_id = inserted_post_id
    item.dedupe_match_post_id = None
    item.processing_notes = "Auto-published from approved source."
    return "published"


async def process_persisted_ingestion_entries(
    *,
    db: AsyncSession,
    source: Source,
    entries: list[PersistedEntryRef],
    now: datetime | None = None,
) -> ProcessIngestionEntriesResult:
    current_time = _utcnow() if now is None else now
    processed_item_count = 0
    published_item_count = 0
    awaiting_review_item_count = 0
    system_user: User | None = None

    for entry in entries:
        item = await _load_ingestion_item_for_entry(db=db, source_id=source.id, entry=entry)
        if item is None:
            continue
        if item.ingestion_status in {
            IngestionStatus.DUPLICATE,
            IngestionStatus.PUBLISHED,
            IngestionStatus.REJECTED,
            IngestionStatus.AWAITING_REVIEW,
        }:
            continue

        item.detected_category = classify_ingestion_category(source=source, title=item.title)
        processed_item_count += 1

        if source.auto_publish:
            if system_user is None:
                system_user = await resolve_or_create_ingestion_system_user(db=db)
            publish_result = await publish_ingestion_item(
                db=db,
                source=source,
                item=item,
                author=system_user,
                now=current_time,
            )
            if publish_result == "published":
                published_item_count += 1
            continue

        item.ingestion_status = IngestionStatus.AWAITING_REVIEW
        item.processing_notes = "Awaiting manual ingestion review."
        awaiting_review_item_count += 1

    return ProcessIngestionEntriesResult(
        processed_item_count=processed_item_count,
        published_item_count=published_item_count,
        awaiting_review_item_count=awaiting_review_item_count,
    )
