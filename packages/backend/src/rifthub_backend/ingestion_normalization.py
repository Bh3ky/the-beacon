from __future__ import annotations

from datetime import UTC, datetime
import re
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_QUERY_PARAM_PREFIXES = ("utm_", "mc_")
TRACKING_QUERY_PARAM_NAMES = {
    "fbclid",
    "gclid",
    "igshid",
    "mkt_tok",
    "ref",
    "ref_src",
    "source",
}

_MULTISPACE_RE = re.compile(r"\s+")
_REPEATED_PUNCTUATION_RE = re.compile(r"([!?.,])\1+")


def _validated_split(raw_url: str) -> SplitResult:
    candidate = raw_url.strip()
    if not candidate:
        raise ValueError("URL is required.")

    split = urlsplit(candidate)
    if split.scheme.lower() not in {"http", "https"} or not split.hostname:
        raise ValueError("URL must use http or https and include a hostname.")
    return split


def _is_tracking_query_param(name: str) -> bool:
    lowered = name.lower()
    return lowered in TRACKING_QUERY_PARAM_NAMES or any(
        lowered.startswith(prefix) for prefix in TRACKING_QUERY_PARAM_PREFIXES
    )


def normalize_external_url(raw_url: str) -> str:
    split = _validated_split(raw_url)
    scheme = split.scheme.lower()
    hostname = split.hostname.lower()
    port = split.port
    netloc = hostname
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"

    query_items = [
        (name, value)
        for name, value in parse_qsl(split.query, keep_blank_values=False)
        if not _is_tracking_query_param(name)
    ]
    query_items.sort()
    normalized = SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=split.path or "",
        query=urlencode(query_items, doseq=True),
        fragment="",
    )
    return urlunsplit(normalized)


def hostname_from_normalized_url(normalized_url: str) -> str:
    return _validated_split(normalized_url).hostname.lower()


def normalize_ingestion_title(raw_title: str) -> str:
    normalized = _MULTISPACE_RE.sub(" ", raw_title.strip())
    normalized = _REPEATED_PUNCTUATION_RE.sub(r"\1", normalized)
    if not normalized:
        raise ValueError("Title is required.")
    return normalized


def normalize_external_published_at(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
