from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from rifthub_backend.db.types import Category, IngestionStatus
from rifthub_backend.ingestion_publication import (
    ProcessIngestionEntriesResult,
    classify_ingestion_category,
    process_persisted_ingestion_entries,
)


def make_source(*, auto_publish: bool, default_category: Category | None = None) -> object:
    return SimpleNamespace(
        id=uuid4(),
        auto_publish=auto_publish,
        default_category=default_category,
    )


def make_item(*, status: IngestionStatus = IngestionStatus.NORMALIZED, title: str = "Startup raises seed funding") -> object:
    return SimpleNamespace(
        id=uuid4(),
        ingestion_status=status,
        title=title,
        url="https://example.com/story-1",
        url_normalized="https://example.com/story-1",
        detected_category=None,
        linked_post_id=None,
        dedupe_match_post_id=None,
        processing_notes=None,
    )


def make_entry(*, external_id: str | None = "story-1") -> object:
    return SimpleNamespace(
        external_id=external_id,
        url="https://example.com/story-1",
    )


def test_classify_ingestion_category_prefers_specific_source_default() -> None:
    source = make_source(auto_publish=False, default_category=Category.POLICY)

    assert classify_ingestion_category(source=source, title="Startup raises seed funding") == Category.POLICY


def test_classify_ingestion_category_uses_keyword_rules_when_source_is_generic() -> None:
    source = make_source(auto_publish=False, default_category=Category.ECOSYSTEM)

    assert classify_ingestion_category(source=source, title="Startup raises seed funding") == Category.FUNDING


@pytest.mark.anyio
async def test_process_persisted_ingestion_entries_marks_review_queue_for_non_auto_publish() -> None:
    source = make_source(auto_publish=False, default_category=Category.ECOSYSTEM)
    item = make_item(title="Startup raises seed funding")

    class FakeDbSession:
        async def scalar(self, _statement: object):
            return item

    result = await process_persisted_ingestion_entries(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        entries=[make_entry()],  # type: ignore[list-item]
        now=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    )

    assert result == ProcessIngestionEntriesResult(
        processed_item_count=1,
        published_item_count=0,
        awaiting_review_item_count=1,
    )
    assert item.ingestion_status == IngestionStatus.AWAITING_REVIEW
    assert item.detected_category == Category.FUNDING
    assert item.processing_notes == "Awaiting manual ingestion review."


@pytest.mark.anyio
async def test_process_persisted_ingestion_entries_auto_publishes_when_source_allows_it(monkeypatch) -> None:
    source = make_source(auto_publish=True, default_category=Category.ECOSYSTEM)
    item = make_item(title="Startup raises seed funding")
    system_user = SimpleNamespace(id=uuid4())
    calls: list[str] = []

    class FakeDbSession:
        async def scalar(self, _statement: object):
            return item

    async def fake_resolve_or_create_ingestion_system_user(**_: object):
        return system_user

    async def fake_publish_ingestion_item(**kwargs: object) -> str:
        calls.append("publish")
        kwargs["item"].ingestion_status = IngestionStatus.PUBLISHED
        return "published"

    monkeypatch.setattr(
        "rifthub_backend.ingestion_publication.resolve_or_create_ingestion_system_user",
        fake_resolve_or_create_ingestion_system_user,
    )
    monkeypatch.setattr(
        "rifthub_backend.ingestion_publication.publish_ingestion_item",
        fake_publish_ingestion_item,
    )

    result = await process_persisted_ingestion_entries(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        entries=[make_entry()],  # type: ignore[list-item]
        now=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    )

    assert result == ProcessIngestionEntriesResult(
        processed_item_count=1,
        published_item_count=1,
        awaiting_review_item_count=0,
    )
    assert item.detected_category == Category.FUNDING
    assert calls == ["publish"]
