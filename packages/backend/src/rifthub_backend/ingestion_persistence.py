from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import IngestionStatus, PostStatus
from rifthub_backend.models.ingestion import IngestionItem
from rifthub_backend.models.post import Post
from rifthub_backend.models.source import Source

EXTERNAL_ID_UNIQUE_CONSTRAINT = "uq_ingestion_items_source_id_external_id"
URL_FALLBACK_UNIQUE_CONSTRAINT = "uq_ingestion_items_source_id_url_normalized_no_external_id"
_PRESERVED_INGESTION_STATUSES = frozenset(
    {
        IngestionStatus.CLASSIFIED,
        IngestionStatus.AWAITING_REVIEW,
        IngestionStatus.PUBLISHED,
        IngestionStatus.REJECTED,
    }
)


class DiscoveredFeedEntry(Protocol):
    external_id: str | None
    title: str
    url: str
    published_at_external: datetime | None
    raw_payload_json: dict[str, object]


@dataclass(frozen=True, slots=True)
class PersistIngestionEntriesResult:
    stored_item_count: int
    normalized_item_count: int
    duplicate_item_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _next_ingestion_status(*, duplicate_post_id: UUID | None) -> IngestionStatus:
    if duplicate_post_id is not None:
        return IngestionStatus.DUPLICATE
    return IngestionStatus.NORMALIZED


def _processing_notes(*, duplicate_post_id: UUID | None) -> str | None:
    if duplicate_post_id is None:
        return None
    return "Matched existing active post by normalized URL."


async def _load_active_posts_by_url(
    *,
    db: AsyncSession,
    urls: set[str],
) -> dict[str, Post]:
    if not urls:
        return {}
    posts = list(
        (
            await db.scalars(
                select(Post).where(
                    Post.status == PostStatus.ACTIVE,
                    Post.url_normalized.in_(sorted(urls)),
                )
            )
        ).all()
    )
    return {post.url_normalized: post for post in posts if post.url_normalized is not None}


def _build_insert_values(
    *,
    source_id: UUID,
    entry: DiscoveredFeedEntry,
    duplicate_post_id: UUID | None,
    now: datetime,
) -> dict[str, object]:
    next_status = _next_ingestion_status(duplicate_post_id=duplicate_post_id)
    return {
        "source_id": source_id,
        "external_id": entry.external_id,
        "title": entry.title,
        "url": entry.url,
        "url_normalized": entry.url,
        "published_at_external": entry.published_at_external,
        "discovered_at": now,
        "ingestion_status": next_status,
        "linked_post_id": None,
        "dedupe_match_post_id": duplicate_post_id,
        "raw_payload_json": entry.raw_payload_json,
        "processing_notes": _processing_notes(duplicate_post_id=duplicate_post_id),
    }


async def _insert_if_missing(
    *,
    db: AsyncSession,
    constraint_name: str,
    values: dict[str, object],
) -> UUID | None:
    statement = (
        pg_insert(IngestionItem)
        .values(**values)
        .on_conflict_do_nothing(constraint=constraint_name)
        .returning(IngestionItem.id)
    )
    return await db.scalar(statement)


async def _load_existing_item(
    *,
    db: AsyncSession,
    source_id: UUID,
    entry: DiscoveredFeedEntry,
) -> IngestionItem:
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
    item = await db.scalar(statement)
    if item is None:  # pragma: no cover - defensive guard against broken transaction flow
        raise RuntimeError("Expected an existing ingestion item after conflict.")
    return item


def _refresh_existing_item(
    *,
    item: IngestionItem,
    entry: DiscoveredFeedEntry,
    duplicate_post_id: UUID | None,
) -> IngestionStatus:
    item.title = entry.title
    item.url = entry.url
    item.url_normalized = entry.url
    item.published_at_external = entry.published_at_external
    item.raw_payload_json = entry.raw_payload_json

    next_status = _next_ingestion_status(duplicate_post_id=duplicate_post_id)
    if item.ingestion_status in _PRESERVED_INGESTION_STATUSES:
        return item.ingestion_status

    item.ingestion_status = next_status
    item.dedupe_match_post_id = duplicate_post_id
    if duplicate_post_id is None:
        item.linked_post_id = None
    item.processing_notes = _processing_notes(duplicate_post_id=duplicate_post_id)
    return next_status


async def persist_discovered_ingestion_entries(
    *,
    db: AsyncSession,
    source: Source,
    entries: list[DiscoveredFeedEntry],
    now: datetime | None = None,
) -> PersistIngestionEntriesResult:
    current_time = _utcnow() if now is None else now
    posts_by_url = await _load_active_posts_by_url(
        db=db,
        urls={entry.url for entry in entries},
    )

    normalized_item_count = 0
    duplicate_item_count = 0
    stored_item_count = 0

    for entry in entries:
        duplicate_post = posts_by_url.get(entry.url)
        duplicate_post_id = duplicate_post.id if duplicate_post is not None else None
        values = _build_insert_values(
            source_id=source.id,
            entry=entry,
            duplicate_post_id=duplicate_post_id,
            now=current_time,
        )
        constraint_name = (
            EXTERNAL_ID_UNIQUE_CONSTRAINT
            if entry.external_id is not None
            else URL_FALLBACK_UNIQUE_CONSTRAINT
        )
        inserted_id = await _insert_if_missing(
            db=db,
            constraint_name=constraint_name,
            values=values,
        )
        if inserted_id is not None:
            stored_item_count += 1
            if duplicate_post_id is None:
                normalized_item_count += 1
            else:
                duplicate_item_count += 1
            continue

        item = await _load_existing_item(db=db, source_id=source.id, entry=entry)
        stored_item_count += 1
        outcome_status = _refresh_existing_item(
            item=item,
            entry=entry,
            duplicate_post_id=duplicate_post_id,
        )
        if outcome_status == IngestionStatus.DUPLICATE:
            duplicate_item_count += 1
        elif outcome_status == IngestionStatus.NORMALIZED:
            normalized_item_count += 1

    return PersistIngestionEntriesResult(
        stored_item_count=stored_item_count,
        normalized_item_count=normalized_item_count,
        duplicate_item_count=duplicate_item_count,
    )
