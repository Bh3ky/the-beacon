from uuid import uuid4

import pytest
from sqlalchemy import select

from rifthub_backend.models.post import Post
from rifthub_backend.reads import ReadError, _apply_feed_cursor, decode_feed_cursor, encode_feed_cursor


def test_feed_cursor_round_trip_for_top_feed() -> None:
    cursor = encode_feed_cursor(
        {"kind": "top", "rank_score": 5.91, "id": "6f694e1d-1d1a-4d53-a59d-a8ab26111a11"}
    )

    payload = decode_feed_cursor(cursor, kind="top")

    assert payload["kind"] == "top"
    assert payload["rank_score"] == 5.91
    assert payload["id"] == "6f694e1d-1d1a-4d53-a59d-a8ab26111a11"


def test_feed_cursor_rejects_wrong_kind() -> None:
    cursor = encode_feed_cursor(
        {"kind": "new", "submitted_at": "2026-03-17T10:00:00+00:00", "id": "6f694e1d-1d1a-4d53-a59d-a8ab26111a11"}
    )

    with pytest.raises(ReadError, match="Cursor is invalid"):
        decode_feed_cursor(cursor, kind="top")


def test_feed_cursor_rejects_malformed_value() -> None:
    with pytest.raises(ReadError, match="Cursor is invalid"):
        decode_feed_cursor("%%%not-a-cursor%%%", kind="top")


def test_feed_cursor_rejects_invalid_json_payload() -> None:
    cursor = "bm90LWpzb24="

    with pytest.raises(ReadError, match="Cursor is invalid"):
        decode_feed_cursor(cursor, kind="top")


def test_apply_feed_cursor_rejects_missing_required_top_fields() -> None:
    cursor = encode_feed_cursor({"kind": "top", "id": str(uuid4())})

    with pytest.raises(ReadError, match="Cursor is invalid"):
        _apply_feed_cursor(query=select(Post), kind="top", cursor=cursor)
