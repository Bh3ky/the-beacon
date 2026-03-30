from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from rifthub_backend.db.types import SourceStatus, SourceType
import rifthub_backend.ingestion_polling as polling_module
from rifthub_backend.ingestion_persistence import PersistIngestionEntriesResult
from rifthub_backend.ingestion_publication import ProcessIngestionEntriesResult
from rifthub_backend.ingestion_polling import (
    ParsedFeedEntry,
    ParsedFeedResult,
    PollSourcesResult,
    SourceFetchResult,
    load_due_rss_sources,
    poll_due_rss_sources,
    poll_rss_source,
    source_is_due,
)


def make_source(
    *,
    last_checked_at: datetime | None,
    poll_interval_minutes: int = 30,
    status: SourceStatus = SourceStatus.ACTIVE,
    source_type: SourceType = SourceType.RSS,
) -> object:
    return SimpleNamespace(
        id=uuid4(),
        status=status,
        source_type=source_type,
        poll_interval_minutes=poll_interval_minutes,
        last_checked_at=last_checked_at,
        last_success_at=None,
        last_error_at=None,
        last_error_message=None,
        last_etag=None,
        last_modified_header=None,
        url="https://example.com/feed.xml",
    )


def test_source_is_due_when_never_checked() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    source = make_source(last_checked_at=None)

    assert source_is_due(source=source, now=now) is True


def test_source_is_due_respects_poll_interval() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    fresh_source = make_source(last_checked_at=now - timedelta(minutes=10), poll_interval_minutes=30)
    stale_source = make_source(last_checked_at=now - timedelta(minutes=31), poll_interval_minutes=30)

    assert source_is_due(source=fresh_source, now=now) is False
    assert source_is_due(source=stale_source, now=now) is True


@pytest.mark.anyio
async def test_load_due_rss_sources_filters_active_rss_sources(monkeypatch) -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    due = make_source(last_checked_at=None)
    not_due = make_source(last_checked_at=now - timedelta(minutes=5))
    paused = make_source(last_checked_at=None, status=SourceStatus.PAUSED)
    non_rss = make_source(last_checked_at=None, source_type=SourceType.API)

    class FakeDbSession:
        async def scalars(self, _query: object):
            return SimpleNamespace(all=lambda: [due, not_due, paused, non_rss])

    result = await load_due_rss_sources(db=FakeDbSession(), now=now, limit=10)  # type: ignore[arg-type]

    assert result == [due]


@pytest.mark.anyio
async def test_poll_rss_source_marks_unchanged_for_304() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    source = make_source(last_checked_at=None)

    class FakeDbSession:
        def __init__(self) -> None:
            self.commits = 0

        async def commit(self) -> None:
            self.commits += 1

    async def fake_fetch(_source: object) -> SourceFetchResult:
        return SourceFetchResult(
            status_code=304,
            body=None,
            etag='"etag-1"',
            last_modified_header="Wed, 24 Mar 2026 11:00:00 GMT",
        )

    result = await poll_rss_source(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        now=now,
        fetch_source_content=fake_fetch,
    )

    assert result.status == "unchanged"
    assert source.last_success_at == now
    assert source.last_etag == '"etag-1"'
    assert result.stored_item_count == 0


@pytest.mark.anyio
async def test_poll_rss_source_marks_failure_when_fetch_raises() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    source = make_source(last_checked_at=None)

    class FakeDbSession:
        async def commit(self) -> None:
            return None

    async def failing_fetch(_source: object) -> SourceFetchResult:
        raise RuntimeError("network down")

    result = await poll_rss_source(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        now=now,
        fetch_source_content=failing_fetch,
    )

    assert result.status == "failed"
    assert source.last_error_message == "network down"


@pytest.mark.anyio
async def test_poll_rss_source_counts_parsed_entries_and_clears_errors() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    source = make_source(last_checked_at=None)
    source.last_error_message = "old failure"

    class FakeDbSession:
        async def commit(self) -> None:
            return None

    async def fake_fetch(_source: object) -> SourceFetchResult:
        return SourceFetchResult(
            status_code=200,
            body=b"<rss />",
            etag=None,
            last_modified_header=None,
        )

    def fake_parse(_body: bytes) -> ParsedFeedResult:
        return ParsedFeedResult(
            entries=[
                ParsedFeedEntry(
                    external_id="story-1",
                    title="Story One",
                    url="https://example.com/story-1",
                    published_at_external=now,
                    raw_payload_json={"title": "Story One"},
                ),
                ParsedFeedEntry(
                    external_id="story-2",
                    title="Story Two",
                    url="https://example.com/story-2",
                    published_at_external=None,
                    raw_payload_json={"title": "Story Two"},
                ),
            ],
            bozo=True,
            bozo_message="minor parse issue",
        )

    async def fake_persist_entries(**_: object) -> PersistIngestionEntriesResult:
        return PersistIngestionEntriesResult(
            stored_item_count=2,
            normalized_item_count=1,
            duplicate_item_count=1,
        )

    async def fake_process_entries(**_: object) -> ProcessIngestionEntriesResult:
        return ProcessIngestionEntriesResult(
            processed_item_count=2,
            published_item_count=1,
            awaiting_review_item_count=1,
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(polling_module, "persist_discovered_ingestion_entries", fake_persist_entries)
    monkeypatch.setattr(polling_module, "process_persisted_ingestion_entries", fake_process_entries)

    try:
        result = await poll_rss_source(
            db=FakeDbSession(),  # type: ignore[arg-type]
            source=source,  # type: ignore[arg-type]
            now=now,
            fetch_source_content=fake_fetch,
            parse_feed_content=fake_parse,
        )
    finally:
        monkeypatch.undo()

    assert result.status == "polled"
    assert result.discovered_entry_count == 2
    assert result.stored_item_count == 2
    assert result.normalized_item_count == 1
    assert result.duplicate_item_count == 1
    assert result.processed_item_count == 2
    assert result.published_item_count == 1
    assert result.awaiting_review_item_count == 1
    assert result.warning_message == "minor parse issue"
    assert source.last_error_message is None


@pytest.mark.anyio
async def test_poll_due_rss_sources_aggregates_results_and_respects_source_lock() -> None:
    source_one = make_source(last_checked_at=None)
    source_two = make_source(last_checked_at=None)

    class FakeLease:
        def __init__(self, events: list[str], source_id: str) -> None:
            self._events = events
            self._source_id = source_id

        async def release(self) -> None:
            self._events.append(f"released:{self._source_id}")

    class FakeLockManager:
        def __init__(self) -> None:
            self.events: list[str] = []

        async def acquire(self, *, job_name: str, lease_seconds: int):
            self.events.append(f"acquire:{job_name}:{lease_seconds}")
            if job_name == str(source_two.id):
                return None
            return FakeLease(self.events, job_name)

        async def aclose(self) -> None:
            return None

    async def fake_load_due_sources(**_: object):
        return [source_one, source_two]

    async def fake_poll_rss_source(**kwargs: object):
        source = kwargs["source"]
        return SimpleNamespace(
            source_id=source.id,
            status="polled",
            discovered_entry_count=3,
            stored_item_count=3,
            normalized_item_count=2,
            duplicate_item_count=1,
            processed_item_count=2,
            published_item_count=1,
            awaiting_review_item_count=1,
            warning_message=None,
            error_message=None,
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(polling_module, "load_due_rss_sources", fake_load_due_sources)
    monkeypatch.setattr(polling_module, "poll_rss_source", fake_poll_rss_source)
    lock_manager = FakeLockManager()

    try:
        result = await poll_due_rss_sources(
            db=object(),  # type: ignore[arg-type]
            source_lock_manager=lock_manager,
        )
    finally:
        monkeypatch.undo()

    assert result == PollSourcesResult(
        selected_source_count=2,
        polled_source_count=1,
        unchanged_source_count=0,
        failed_source_count=0,
        discovered_entry_count=3,
        stored_item_count=3,
        normalized_item_count=2,
        duplicate_item_count=1,
        processed_item_count=2,
        published_item_count=1,
        awaiting_review_item_count=1,
    )
    assert any(event.startswith(f"released:{source_one.id}") for event in lock_manager.events)


@pytest.mark.anyio
async def test_poll_rss_source_marks_failure_when_persistence_raises() -> None:
    now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
    source = make_source(last_checked_at=None)

    class FakeDbSession:
        def __init__(self) -> None:
            self.rolled_back = False
            self.commits = 0

        async def rollback(self) -> None:
            self.rolled_back = True

        async def commit(self) -> None:
            self.commits += 1

    async def fake_fetch(_source: object) -> SourceFetchResult:
        return SourceFetchResult(
            status_code=200,
            body=b"<rss />",
            etag=None,
            last_modified_header=None,
        )

    def fake_parse(_body: bytes) -> ParsedFeedResult:
        return ParsedFeedResult(
            entries=[
                ParsedFeedEntry(
                    external_id="story-1",
                    title="Story One",
                    url="https://example.com/story-1",
                    published_at_external=now,
                    raw_payload_json={"title": "Story One"},
                )
            ],
        )

    async def failing_persist(**_: object) -> PersistIngestionEntriesResult:
        raise RuntimeError("persistence failed")

    db = FakeDbSession()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(polling_module, "persist_discovered_ingestion_entries", failing_persist)

    try:
        result = await poll_rss_source(
            db=db,  # type: ignore[arg-type]
            source=source,  # type: ignore[arg-type]
            now=now,
            fetch_source_content=fake_fetch,
            parse_feed_content=fake_parse,
        )
    finally:
        monkeypatch.undo()

    assert result.status == "failed"
    assert result.error_message == "persistence failed"
    assert db.rolled_back is True
    assert db.commits == 1
    assert source.last_error_message == "persistence failed"
