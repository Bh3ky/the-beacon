from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from rifthub_backend.db.types import IngestionStatus, PostStatus
from rifthub_backend.ingestion_persistence import persist_discovered_ingestion_entries


def make_entry(
    *,
    external_id: str | None,
    title: str = "Story One",
    url: str = "https://example.com/story-1",
) -> object:
    return SimpleNamespace(
        external_id=external_id,
        title=title,
        url=url,
        published_at_external=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
        raw_payload_json={"title": title, "url": url},
    )


@pytest.mark.anyio
async def test_persist_discovered_ingestion_entries_updates_existing_duplicate_item() -> None:
    source = SimpleNamespace(id=uuid4())
    duplicate_post = SimpleNamespace(
        id=uuid4(),
        status=PostStatus.ACTIVE,
        url_normalized="https://example.com/story-1",
    )
    existing_item = SimpleNamespace(
        ingestion_status=IngestionStatus.NORMALIZED,
        title="Old title",
        url="https://example.com/old",
        url_normalized="https://example.com/old",
        published_at_external=None,
        raw_payload_json=None,
        linked_post_id=None,
        dedupe_match_post_id=None,
        processing_notes=None,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.scalar_calls = 0

        async def scalars(self, _statement: object):
            return SimpleNamespace(all=lambda: [duplicate_post])

        async def scalar(self, _statement: object):
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return None
            return existing_item

    result = await persist_discovered_ingestion_entries(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        entries=[make_entry(external_id="source-story-1")],  # type: ignore[list-item]
        now=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    )

    assert result.stored_item_count == 1
    assert result.duplicate_item_count == 1
    assert result.normalized_item_count == 0
    assert existing_item.ingestion_status == IngestionStatus.DUPLICATE
    assert existing_item.dedupe_match_post_id == duplicate_post.id
    assert existing_item.processing_notes == "Matched existing active post by normalized URL."


@pytest.mark.anyio
async def test_persist_discovered_ingestion_entries_preserves_published_item_status() -> None:
    source = SimpleNamespace(id=uuid4())
    existing_item = SimpleNamespace(
        ingestion_status=IngestionStatus.PUBLISHED,
        title="Old title",
        url="https://example.com/old",
        url_normalized="https://example.com/old",
        published_at_external=None,
        raw_payload_json={"old": True},
        linked_post_id=uuid4(),
        dedupe_match_post_id=None,
        processing_notes="already published",
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.scalar_calls = 0

        async def scalars(self, _statement: object):
            return SimpleNamespace(all=lambda: [])

        async def scalar(self, _statement: object):
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return None
            return existing_item

    entry = make_entry(external_id="source-story-1", title="Fresh title")
    result = await persist_discovered_ingestion_entries(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        entries=[entry],  # type: ignore[list-item]
        now=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    )

    assert result.stored_item_count == 1
    assert result.duplicate_item_count == 0
    assert result.normalized_item_count == 0
    assert existing_item.ingestion_status == IngestionStatus.PUBLISHED
    assert existing_item.title == "Fresh title"
    assert existing_item.processing_notes == "already published"


@pytest.mark.anyio
async def test_persist_discovered_ingestion_entries_uses_url_fallback_when_external_id_missing() -> None:
    source = SimpleNamespace(id=uuid4())
    existing_item = SimpleNamespace(
        ingestion_status=IngestionStatus.DISCOVERED,
        title="Old title",
        url="https://example.com/old",
        url_normalized="https://example.com/old",
        published_at_external=None,
        raw_payload_json={"old": True},
        linked_post_id=None,
        dedupe_match_post_id=None,
        processing_notes=None,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.scalar_calls = 0

        async def scalars(self, _statement: object):
            return SimpleNamespace(all=lambda: [])

        async def scalar(self, _statement: object):
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return None
            return existing_item

    result = await persist_discovered_ingestion_entries(
        db=FakeDbSession(),  # type: ignore[arg-type]
        source=source,  # type: ignore[arg-type]
        entries=[make_entry(external_id=None)],  # type: ignore[list-item]
        now=datetime(2026, 3, 24, 12, 0, tzinfo=UTC),
    )

    assert result.stored_item_count == 1
    assert result.normalized_item_count == 1
    assert result.duplicate_item_count == 0
    assert existing_item.ingestion_status == IngestionStatus.NORMALIZED
    assert existing_item.url_normalized == "https://example.com/story-1"
