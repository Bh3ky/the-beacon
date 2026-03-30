from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

import rifthub_backend.ingestion_sources as ingestion_sources_module
from rifthub_backend.db.types import Category, SourceStatus, SourceType
from rifthub_backend.ingestion_normalization import (
    hostname_from_normalized_url,
    normalize_external_published_at,
    normalize_external_url,
    normalize_ingestion_title,
)
from rifthub_backend.ingestion_sources import (
    ApprovedSourceInput,
    SourceImportError,
    import_approved_sources,
    load_approved_sources,
    parse_approved_source,
)


def test_normalize_external_url_strips_tracking_fragment_and_default_port() -> None:
    normalized = normalize_external_url(
        " HTTPS://Example.COM:443/story?utm_source=x&b=2&a=1#comments "
    )

    assert normalized == "https://example.com/story?a=1&b=2"
    assert hostname_from_normalized_url(normalized) == "example.com"


def test_normalize_external_url_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="URL must use http or https"):
        normalize_external_url("ftp://example.com/story")


def test_normalize_ingestion_title_collapses_whitespace_and_duplicate_punctuation() -> None:
    assert normalize_ingestion_title("  RiftHub   raises!!!  ") == "RiftHub raises!"


def test_normalize_external_published_at_converts_to_utc() -> None:
    naive = datetime(2026, 3, 24, 10, 0, 0)
    aware = datetime(2026, 3, 24, 12, 0, 0, tzinfo=UTC)

    assert normalize_external_published_at(naive) == datetime(2026, 3, 24, 10, 0, 0, tzinfo=UTC)
    assert normalize_external_published_at(aware) == aware


def test_parse_approved_source_uses_first_supported_category_and_normalizes_urls() -> None:
    parsed = parse_approved_source(
        {
            "name": "TechCabal",
            "source_type": "rss",
            "status": "active",
            "feed_url": "https://techcabal.com/feed/?utm_source=rss",
            "base_url": "https://TechCabal.com",
            "categories": ["news", "funding"],
            "trust_score": "0.85",
            "auto_publish": True,
            "poll_interval_minutes": 15,
        }
    )

    assert parsed.url == "https://techcabal.com/feed/"
    assert parsed.site_url == "https://techcabal.com"
    assert parsed.default_category == Category.ECOSYSTEM
    assert parsed.trust_score == Decimal("0.85")


def test_load_approved_sources_reads_seed_file() -> None:
    sources = load_approved_sources(Path("scripts/seed-data/approved_sources.dev.json"))

    assert len(sources) == 5
    assert sources[0].source_type == SourceType.RSS


def test_parse_approved_source_requires_url_field() -> None:
    with pytest.raises(SourceImportError, match="usable source URL"):
        parse_approved_source(
            {
                "name": "Broken source",
                "source_type": "rss",
                "status": "active",
            }
        )


@pytest.mark.anyio
async def test_import_approved_sources_inserts_and_updates_rows(monkeypatch) -> None:
    domain = SimpleNamespace(id=uuid4())
    existing_source = SimpleNamespace(
        name="Existing",
        source_type=SourceType.RSS,
        status=SourceStatus.PAUSED,
        url="https://example.com/feed.xml",
        site_url="https://example.com",
        default_category=None,
        domain_id=None,
        trust_score=Decimal("0.50"),
        auto_publish=False,
        poll_interval_minutes=60,
    )

    class FakeDbSession:
        def __init__(self) -> None:
            self.scalar_calls = 0
            self.added: list[object] = []
            self.flushed = False
            self.committed = False

        async def scalar(self, _query: object) -> object | None:
            self.scalar_calls += 1
            if self.scalar_calls == 1:
                return None
            return existing_source

        def add(self, obj: object) -> None:
            self.added.append(obj)

        async def flush(self) -> None:
            self.flushed = True

        async def commit(self) -> None:
            self.committed = True

    async def fake_resolve_or_create_domain(**_: object) -> object:
        return domain

    monkeypatch.setattr(
        ingestion_sources_module,
        "resolve_or_create_domain",
        fake_resolve_or_create_domain,
    )

    db = FakeDbSession()
    result = await import_approved_sources(
        db=db,  # type: ignore[arg-type]
        source_inputs=[
            ApprovedSourceInput(
                name="Inserted source",
                source_type=SourceType.RSS,
                status=SourceStatus.ACTIVE,
                url="https://inserted.example/feed.xml",
                site_url="https://inserted.example",
                default_category=Category.FUNDING,
                trust_score=Decimal("0.90"),
                auto_publish=True,
                poll_interval_minutes=30,
            ),
            ApprovedSourceInput(
                name="Updated source",
                source_type=SourceType.RSS,
                status=SourceStatus.ACTIVE,
                url="https://example.com/feed.xml",
                site_url="https://example.com",
                default_category=Category.POLICY,
                trust_score=Decimal("0.75"),
                auto_publish=True,
                poll_interval_minutes=15,
            ),
        ],
    )

    assert result.inserted_count == 1
    assert result.updated_count == 1
    assert db.flushed is True
    assert db.committed is True
    assert len(db.added) == 1
    assert db.added[0].url == "https://inserted.example/feed.xml"
    assert db.added[0].domain_id == domain.id
    assert existing_source.default_category == Category.POLICY
    assert existing_source.auto_publish is True
    assert existing_source.poll_interval_minutes == 15
