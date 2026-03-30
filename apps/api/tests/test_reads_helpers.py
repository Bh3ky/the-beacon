from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

import rifthub_backend.reads as reads_module
from rifthub_backend.db.types import UserRole
from rifthub_backend.models.post import Post
from rifthub_backend.reads import ReadError, _apply_feed_cursor, decode_feed_cursor, encode_feed_cursor


def test_feed_cursor_round_trip_for_top_feed() -> None:
    cursor = encode_feed_cursor(
        {
            "kind": "top",
            "rank_score": 5.91,
            "submitted_at": "2026-03-17T10:00:00+00:00",
            "comment_count": 7,
            "id": "6f694e1d-1d1a-4d53-a59d-a8ab26111a11",
        }
    )

    payload = decode_feed_cursor(cursor, kind="top")

    assert payload["kind"] == "top"
    assert payload["rank_score"] == 5.91
    assert payload["submitted_at"] == "2026-03-17T10:00:00+00:00"
    assert payload["comment_count"] == 7
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


class FakeScalarResult:
    def unique(self):
        return self

    def all(self):
        return []


class FakeResult:
    def scalars(self):
        return FakeScalarResult()


class CapturingDbSession:
    def __init__(self) -> None:
        self.statements: list[object] = []
        self.scalar_value: object | None = None

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult()

    async def scalar(self, _statement):
        return self.scalar_value


def compile_sql(statement: object) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.mark.anyio
async def test_get_top_feed_query_excludes_jobs_uses_blocked_domain_filter_and_rank_tiebreakers(monkeypatch) -> None:
    db = CapturingDbSession()

    async def fake_viewer_post_votes(**_: object) -> dict:
        return {}

    monkeypatch.setattr(reads_module, "_viewer_post_votes", fake_viewer_post_votes)

    page = await reads_module.get_top_feed(
        db=db,  # type: ignore[arg-type]
        limit=20,
        cursor=None,
        viewer_user_id=None,
        viewer_role=UserRole.USER,
    )

    assert page.items == []
    compiled = compile_sql(db.statements[0])
    assert "posts.post_type !=" in compiled
    assert "posts.status = 'active'" in compiled
    assert "domains.is_blocked is false" in compiled.lower()
    assert "ORDER BY posts.rank_score DESC, posts.submitted_at DESC, posts.comment_count DESC, posts.id DESC" in compiled


@pytest.mark.anyio
async def test_get_ask_feed_query_filters_category_and_reuses_rank_tiebreakers(monkeypatch) -> None:
    db = CapturingDbSession()

    async def fake_viewer_post_votes(**_: object) -> dict:
        return {}

    monkeypatch.setattr(reads_module, "_viewer_post_votes", fake_viewer_post_votes)

    await reads_module.get_ask_feed(
        db=db,  # type: ignore[arg-type]
        limit=20,
        cursor=None,
        viewer_user_id=None,
        viewer_role=None,
    )

    compiled = compile_sql(db.statements[0])
    assert "posts.category = 'ask'" in compiled
    assert "ORDER BY posts.rank_score DESC, posts.submitted_at DESC, posts.comment_count DESC, posts.id DESC" in compiled


@pytest.mark.anyio
async def test_get_jobs_feed_query_is_recency_first_and_filters_expired_jobs(monkeypatch) -> None:
    db = CapturingDbSession()

    async def fake_viewer_post_votes(**_: object) -> dict:
        return {}

    monkeypatch.setattr(reads_module, "_viewer_post_votes", fake_viewer_post_votes)

    await reads_module.get_jobs_feed(
        db=db,  # type: ignore[arg-type]
        limit=20,
        cursor=None,
        viewer_user_id=None,
        viewer_role=None,
    )

    compiled = compile_sql(db.statements[0])
    assert "posts.post_type = 'job'" in compiled
    assert "posts.job_expires_at IS NULL OR posts.job_expires_at >" in compiled
    assert "ORDER BY posts.submitted_at DESC, posts.id DESC" in compiled


@pytest.mark.anyio
async def test_get_post_comments_top_sort_uses_rank_then_created_at_then_id(monkeypatch) -> None:
    db = CapturingDbSession()
    db.scalar_value = uuid4()

    async def fake_viewer_comment_votes(**_: object) -> dict:
        return {}

    monkeypatch.setattr(reads_module, "_viewer_comment_votes", fake_viewer_comment_votes)

    page = await reads_module.get_post_comments(
        db=db,  # type: ignore[arg-type]
        post_id=uuid4(),
        sort="top",
        viewer_user_id=None,
        viewer_role=None,
    )

    assert page.items == []
    assert len(db.statements) == 1
    compiled = compile_sql(db.statements[0])
    assert "FROM comments" in compiled
    assert "comments.status = 'active'" in compiled
    assert "ORDER BY comments.rank_score DESC, comments.created_at DESC, comments.id DESC" in compiled
