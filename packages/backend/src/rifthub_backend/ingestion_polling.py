from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from time import struct_time
from typing import Any, Awaitable, Callable, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import SourceStatus, SourceType
from rifthub_backend.ingestion_persistence import persist_discovered_ingestion_entries
from rifthub_backend.ingestion_publication import process_persisted_ingestion_entries
from rifthub_backend.ingestion_normalization import (
    normalize_external_published_at,
    normalize_external_url,
    normalize_ingestion_title,
)
from rifthub_backend.models.source import Source

logger = logging.getLogger(__name__)

RSS_REQUEST_TIMEOUT_SECONDS = 15
RSS_USER_AGENT = "RiftHubBot/0.1 (+https://rifthub.local)"
SOURCE_POLL_LOCK_PREFIX = "rifthub:worker-lock:source"
SOURCE_POLL_LOCK_TTL_SECONDS = 120


class SourcePollLockManager(Protocol):
    async def acquire(self, *, job_name: str, lease_seconds: int) -> Any | None: ...

    async def aclose(self) -> None: ...


@dataclass(frozen=True, slots=True)
class SourceFetchResult:
    status_code: int
    body: bytes | None
    etag: str | None
    last_modified_header: str | None


@dataclass(frozen=True, slots=True)
class ParsedFeedEntry:
    external_id: str | None
    title: str
    url: str
    published_at_external: datetime | None
    raw_payload_json: dict[str, object]


@dataclass(frozen=True, slots=True)
class ParsedFeedResult:
    entries: list[ParsedFeedEntry]
    bozo: bool = False
    bozo_message: str | None = None


@dataclass(frozen=True, slots=True)
class PollSourceResult:
    source_id: UUID
    status: str
    discovered_entry_count: int = 0
    stored_item_count: int = 0
    normalized_item_count: int = 0
    duplicate_item_count: int = 0
    processed_item_count: int = 0
    published_item_count: int = 0
    awaiting_review_item_count: int = 0
    warning_message: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class PollSourcesResult:
    selected_source_count: int
    polled_source_count: int
    unchanged_source_count: int
    failed_source_count: int
    discovered_entry_count: int
    stored_item_count: int
    normalized_item_count: int
    duplicate_item_count: int
    processed_item_count: int
    published_item_count: int
    awaiting_review_item_count: int


FetchSourceContent = Callable[[Source], Awaitable[SourceFetchResult]]
ParseFeedContent = Callable[[bytes], ParsedFeedResult]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _struct_time_to_datetime(value: struct_time | None) -> datetime | None:
    if value is None:
        return None
    return datetime(
        value.tm_year,
        value.tm_mon,
        value.tm_mday,
        value.tm_hour,
        value.tm_min,
        value.tm_sec,
        tzinfo=UTC,
    )


def source_is_due(*, source: Source, now: datetime) -> bool:
    if source.status != SourceStatus.ACTIVE or source.source_type != SourceType.RSS:
        return False
    if source.last_checked_at is None:
        return True
    return source.last_checked_at + timedelta(minutes=source.poll_interval_minutes) <= now


async def load_due_rss_sources(
    *,
    db: AsyncSession,
    now: datetime | None = None,
    limit: int = 25,
) -> list[Source]:
    current_time = _utcnow() if now is None else now
    sources = list(
        (
            await db.scalars(
                select(Source)
                .where(Source.source_type == SourceType.RSS, Source.status == SourceStatus.ACTIVE)
                .order_by(Source.last_checked_at.asc().nullsfirst(), Source.id.asc())
            )
        ).all()
    )
    return [source for source in sources if source_is_due(source=source, now=current_time)][:limit]


async def default_fetch_source_content(source: Source) -> SourceFetchResult:
    import aiohttp

    headers = {
        "User-Agent": RSS_USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }
    if source.last_etag:
        headers["If-None-Match"] = source.last_etag
    if source.last_modified_header:
        headers["If-Modified-Since"] = source.last_modified_header

    timeout = aiohttp.ClientTimeout(total=RSS_REQUEST_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(source.url) as response:
            body = None if response.status == 304 else await response.read()
            return SourceFetchResult(
                status_code=response.status,
                body=body,
                etag=response.headers.get("ETag"),
                last_modified_header=response.headers.get("Last-Modified"),
            )


def default_parse_feed_content(body: bytes) -> ParsedFeedResult:
    try:
        import feedparser
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env packaging
        raise RuntimeError("feedparser package is required for RSS polling.") from exc

    parsed = feedparser.parse(body)
    entries: list[ParsedFeedEntry] = []
    for entry in parsed.entries:
        raw_url = getattr(entry, "link", None)
        raw_title = getattr(entry, "title", None)
        if not raw_url or not raw_title:
            continue
        try:
            normalized_url = normalize_external_url(str(raw_url))
            normalized_title = normalize_ingestion_title(str(raw_title))
        except ValueError:
            continue

        published_at = normalize_external_published_at(
            _struct_time_to_datetime(
                getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            )
        )
        raw_payload_json = {
            "title": str(raw_title),
            "url": str(raw_url),
        }
        raw_id = getattr(entry, "id", None)
        if raw_id is not None:
            raw_payload_json["id"] = str(raw_id)
        entries.append(
            ParsedFeedEntry(
                external_id=str(raw_id) if raw_id is not None else None,
                title=normalized_title,
                url=normalized_url,
                published_at_external=published_at,
                raw_payload_json=raw_payload_json,
            )
        )

    bozo = bool(getattr(parsed, "bozo", 0))
    bozo_exception = getattr(parsed, "bozo_exception", None)
    return ParsedFeedResult(
        entries=entries,
        bozo=bozo,
        bozo_message=str(bozo_exception) if bozo_exception is not None else None,
    )


async def poll_rss_source(
    *,
    db: AsyncSession,
    source: Source,
    now: datetime | None = None,
    fetch_source_content: FetchSourceContent = default_fetch_source_content,
    parse_feed_content: ParseFeedContent = default_parse_feed_content,
) -> PollSourceResult:
    current_time = _utcnow() if now is None else now
    source.last_checked_at = current_time

    try:
        fetched = await fetch_source_content(source)
    except Exception as exc:
        source.last_error_at = current_time
        source.last_error_message = str(exc)
        await db.commit()
        return PollSourceResult(
            source_id=source.id,
            status="failed",
            error_message=str(exc),
        )

    if fetched.etag is not None:
        source.last_etag = fetched.etag
    if fetched.last_modified_header is not None:
        source.last_modified_header = fetched.last_modified_header

    if fetched.status_code == 304:
        source.last_success_at = current_time
        source.last_error_at = None
        source.last_error_message = None
        await db.commit()
        return PollSourceResult(source_id=source.id, status="unchanged")

    if fetched.status_code >= 400 or fetched.body is None:
        message = f"Source returned HTTP {fetched.status_code}."
        source.last_error_at = current_time
        source.last_error_message = message
        await db.commit()
        return PollSourceResult(
            source_id=source.id,
            status="failed",
            error_message=message,
        )

    parsed = parse_feed_content(fetched.body)
    warning_message = parsed.bozo_message if parsed.bozo else None
    if parsed.bozo and not parsed.entries:
        source.last_error_at = current_time
        source.last_error_message = warning_message or "Feed parsing failed."
        await db.commit()
        return PollSourceResult(
            source_id=source.id,
            status="failed",
            error_message=source.last_error_message,
        )

    try:
        persistence_result = await persist_discovered_ingestion_entries(
            db=db,
            source=source,
            entries=parsed.entries,
            now=current_time,
        )
        publication_result = await process_persisted_ingestion_entries(
            db=db,
            source=source,
            entries=parsed.entries,
            now=current_time,
        )
    except Exception as exc:
        await db.rollback()
        source.last_checked_at = current_time
        source.last_error_at = current_time
        source.last_error_message = str(exc)
        await db.commit()
        return PollSourceResult(
            source_id=source.id,
            status="failed",
            error_message=str(exc),
        )

    source.last_success_at = current_time
    source.last_error_at = None
    source.last_error_message = None
    await db.commit()
    return PollSourceResult(
        source_id=source.id,
        status="polled",
        discovered_entry_count=len(parsed.entries),
        stored_item_count=persistence_result.stored_item_count,
        normalized_item_count=persistence_result.normalized_item_count,
        duplicate_item_count=persistence_result.duplicate_item_count,
        processed_item_count=publication_result.processed_item_count,
        published_item_count=publication_result.published_item_count,
        awaiting_review_item_count=publication_result.awaiting_review_item_count,
        warning_message=warning_message,
    )


async def poll_due_rss_sources(
    *,
    db: AsyncSession,
    now: datetime | None = None,
    limit: int = 25,
    source_lock_manager: SourcePollLockManager | None = None,
    fetch_source_content: FetchSourceContent = default_fetch_source_content,
    parse_feed_content: ParseFeedContent = default_parse_feed_content,
) -> PollSourcesResult:
    due_sources = await load_due_rss_sources(db=db, now=now, limit=limit)
    polled_source_count = 0
    unchanged_source_count = 0
    failed_source_count = 0
    discovered_entry_count = 0
    stored_item_count = 0
    normalized_item_count = 0
    duplicate_item_count = 0
    processed_item_count = 0
    published_item_count = 0
    awaiting_review_item_count = 0

    for source in due_sources:
        lease = None
        if source_lock_manager is not None:
            lease = await source_lock_manager.acquire(
                job_name=str(source.id),
                lease_seconds=SOURCE_POLL_LOCK_TTL_SECONDS,
            )
            if lease is None:
                logger.info("poll_rss_sources skipped source due to active lock: %s", source.id)
                continue

        try:
            result = await poll_rss_source(
                db=db,
                source=source,
                now=now,
                fetch_source_content=fetch_source_content,
                parse_feed_content=parse_feed_content,
            )
        finally:
            if lease is not None:
                await lease.release()

        if result.status == "polled":
            polled_source_count += 1
            discovered_entry_count += result.discovered_entry_count
            stored_item_count += result.stored_item_count
            normalized_item_count += result.normalized_item_count
            duplicate_item_count += result.duplicate_item_count
            processed_item_count += result.processed_item_count
            published_item_count += result.published_item_count
            awaiting_review_item_count += result.awaiting_review_item_count
        elif result.status == "unchanged":
            unchanged_source_count += 1
        else:
            failed_source_count += 1

    return PollSourcesResult(
        selected_source_count=len(due_sources),
        polled_source_count=polled_source_count,
        unchanged_source_count=unchanged_source_count,
        failed_source_count=failed_source_count,
        discovered_entry_count=discovered_entry_count,
        stored_item_count=stored_item_count,
        normalized_item_count=normalized_item_count,
        duplicate_item_count=duplicate_item_count,
        processed_item_count=processed_item_count,
        published_item_count=published_item_count,
        awaiting_review_item_count=awaiting_review_item_count,
    )
