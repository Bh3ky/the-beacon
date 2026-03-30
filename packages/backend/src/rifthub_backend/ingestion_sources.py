from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.db.types import Category, SourceStatus, SourceType
from rifthub_backend.domains import resolve_or_create_domain
from rifthub_backend.ingestion_normalization import hostname_from_normalized_url, normalize_external_url
from rifthub_backend.models.source import Source

_CATEGORY_ALIASES = {
    "news": Category.ECOSYSTEM,
}


@dataclass(slots=True)
class SourceImportError(Exception):
    message: str


@dataclass(frozen=True, slots=True)
class ApprovedSourceInput:
    name: str
    source_type: SourceType
    status: SourceStatus
    url: str
    site_url: str | None
    default_category: Category | None
    trust_score: Decimal
    auto_publish: bool
    poll_interval_minutes: int


@dataclass(frozen=True, slots=True)
class SourceImportResult:
    inserted_count: int
    updated_count: int


def _coerce_decimal(raw_value: object, *, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError) as exc:
        raise SourceImportError(f"{field_name} must be a decimal-compatible value.") from exc
    if decimal_value <= 0:
        raise SourceImportError(f"{field_name} must be greater than zero.")
    return decimal_value


def _pick_source_url(payload: dict[str, Any]) -> str:
    for field_name in ("feed_url", "api_endpoint", "entry_url", "url"):
        raw_value = payload.get(field_name)
        if isinstance(raw_value, str) and raw_value.strip():
            return normalize_external_url(raw_value)
    raise SourceImportError("Source entry is missing a usable source URL.")


def _coerce_category(raw_value: object) -> Category | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, Category):
        return raw_value
    if isinstance(raw_value, str):
        candidate = raw_value.strip().lower()
        if not candidate:
            return None
        if candidate in _CATEGORY_ALIASES:
            return _CATEGORY_ALIASES[candidate]
        try:
            return Category(candidate)
        except ValueError:
            return None
    return None


def _pick_default_category(payload: dict[str, Any]) -> Category | None:
    explicit = _coerce_category(payload.get("default_category"))
    if explicit is not None:
        return explicit

    categories = payload.get("categories")
    if not isinstance(categories, list):
        return None

    for value in categories:
        category = _coerce_category(value)
        if category is not None:
            return category
    return None


def parse_approved_source(payload: dict[str, Any]) -> ApprovedSourceInput:
    try:
        name = str(payload["name"]).strip()
        source_type = SourceType(str(payload["source_type"]).strip().lower())
        status = SourceStatus(str(payload["status"]).strip().lower())
    except KeyError as exc:
        raise SourceImportError(f"Missing required source field: {exc.args[0]}") from exc
    except ValueError as exc:
        raise SourceImportError("Source entry contains an invalid enum value.") from exc

    if not name:
        raise SourceImportError("Source name is required.")

    source_url = _pick_source_url(payload)
    site_url = payload.get("site_url") or payload.get("base_url")
    normalized_site_url = None
    if isinstance(site_url, str) and site_url.strip():
        normalized_site_url = normalize_external_url(site_url)

    poll_interval_minutes = int(payload.get("poll_interval_minutes", 30))
    if poll_interval_minutes <= 0:
        raise SourceImportError("poll_interval_minutes must be greater than zero.")

    return ApprovedSourceInput(
        name=name,
        source_type=source_type,
        status=status,
        url=source_url,
        site_url=normalized_site_url,
        default_category=_pick_default_category(payload),
        trust_score=_coerce_decimal(payload.get("trust_score", "1.00"), field_name="trust_score"),
        auto_publish=bool(payload.get("auto_publish", False)),
        poll_interval_minutes=poll_interval_minutes,
    )


def load_approved_sources(path: str | Path) -> list[ApprovedSourceInput]:
    payload = json.loads(Path(path).read_text())
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise SourceImportError("Approved source file must contain a top-level 'sources' array.")
    return [parse_approved_source(source_payload) for source_payload in sources]


async def import_approved_sources(
    *,
    db: AsyncSession,
    source_inputs: list[ApprovedSourceInput],
) -> SourceImportResult:
    inserted_count = 0
    updated_count = 0

    for source_input in source_inputs:
        domain_hostname = hostname_from_normalized_url(source_input.site_url or source_input.url)
        domain = await resolve_or_create_domain(db=db, hostname=domain_hostname)

        existing_source = await db.scalar(select(Source).where(Source.url == source_input.url))
        if existing_source is None:
            existing_source = Source(
                name=source_input.name,
                source_type=source_input.source_type,
                status=source_input.status,
                url=source_input.url,
                site_url=source_input.site_url,
                default_category=source_input.default_category,
                domain_id=domain.id,
                trust_score=source_input.trust_score,
                auto_publish=source_input.auto_publish,
                poll_interval_minutes=source_input.poll_interval_minutes,
            )
            db.add(existing_source)
            inserted_count += 1
            continue

        existing_source.name = source_input.name
        existing_source.source_type = source_input.source_type
        existing_source.status = source_input.status
        existing_source.site_url = source_input.site_url
        existing_source.default_category = source_input.default_category
        existing_source.domain_id = domain.id
        existing_source.trust_score = source_input.trust_score
        existing_source.auto_publish = source_input.auto_publish
        existing_source.poll_interval_minutes = source_input.poll_interval_minutes
        updated_count += 1

    await db.flush()
    await db.commit()
    return SourceImportResult(inserted_count=inserted_count, updated_count=updated_count)
