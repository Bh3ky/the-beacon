from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.auth.service import CurrentSession
from rifthub_backend.config import Settings
from rifthub_backend.db.types import CommentStatus, PostStatus, PostType, UserRole, UserStatus
from rifthub_backend.reads import CommentPage, CommentRead, DomainSummary, FeedPage, PageInfo, PostRead, ReadError, UserSummary

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.feeds as feeds_module
import rifthub_api.routes.posts as posts_module


def make_settings() -> Settings:
    return Settings(
        environment="test",
        log_level="INFO",
        api_host="127.0.0.1",
        api_port=8000,
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        sql_echo=False,
        app_secret="test-secret",
        verification_delivery_mode="noop",
    )


def make_current_session() -> CurrentSession:
    user_id = uuid4()
    return CurrentSession(
        user=SimpleNamespace(
            id=user_id,
            username="bheki",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        ),
        session=SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            session_token_hash="hash",
            expires_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        ),
        csrf_token="csrf-token",
    )


def make_post_read(*, viewer_vote: int | None = None, job_expires_at: datetime | None = None) -> PostRead:
    now = datetime.now(UTC)
    return PostRead(
        id=uuid4(),
        title="African startups are rethinking logistics infrastructure",
        slug="african-startups-are-rethinking-logistics-infrastructure",
        post_type=PostType.LINK if job_expires_at is None else PostType.JOB,
        category="ecosystem" if job_expires_at is None else "jobs",
        status=PostStatus.ACTIVE,
        url="https://example.com/story",
        body_markdown=None,
        author=UserSummary(id=uuid4(), username="bheki"),
        domain=DomainSummary(id=uuid4(), hostname="example.com", display_name="Example"),
        upvote_count=18,
        downvote_count=0,
        comment_count=7,
        score=18,
        rank_score=5.9142,
        viewer_vote=viewer_vote,
        viewer_can_edit=False,
        viewer_can_moderate=False,
        submitted_at=now,
        created_at=now,
        updated_at=now,
        last_commented_at=now,
        job_expires_at=job_expires_at,
    )


def make_category_post_read(category: str) -> PostRead:
    return replace(make_post_read(), category=category)


def make_comment_read(*, parent_comment_id=None, depth: int = 0, viewer_vote: int | None = None) -> CommentRead:
    now = datetime.now(UTC)
    return CommentRead(
        id=uuid4(),
        post_id=uuid4(),
        parent_comment_id=parent_comment_id,
        depth=depth,
        body_markdown="This is one of the more interesting logistics pivots I have seen recently.",
        status=CommentStatus.ACTIVE,
        author=UserSummary(id=uuid4(), username="bheki"),
        upvote_count=5,
        downvote_count=0,
        score=5,
        rank_score=2.12,
        viewer_vote=viewer_vote,
        viewer_can_edit=False,
        viewer_can_moderate=False,
        created_at=now,
        updated_at=now,
    )


def build_client(monkeypatch, *, current_session: CurrentSession | None = None) -> TestClient:
    app_settings = make_settings()
    fake_engine = object()

    async def fake_ping_database(engine: object | None = None) -> None:
        assert engine is fake_engine

    async def fake_dispose_engine() -> None:
        return None

    async def fake_get_db_session() -> AsyncIterator[object]:
        yield object()

    monkeypatch.setattr(main_module, "get_settings", lambda: app_settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: fake_engine)
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_dispose_engine)

    app = main_module.create_app()
    app.dependency_overrides[dependencies_module.get_db_session] = fake_get_db_session
    app.dependency_overrides[dependencies_module.get_settings] = lambda: app_settings
    if current_session is not None:
        async def fake_current_session() -> CurrentSession:
            return current_session

        app.dependency_overrides[dependencies_module.get_current_session] = fake_current_session
    return TestClient(app)


def test_top_feed_returns_expected_envelope(monkeypatch) -> None:
    feed_page = FeedPage(
        items=[make_post_read()],
        page_info=PageInfo(next_cursor="opaque-cursor", has_next_page=True),
    )

    async def fake_get_top_feed(**kwargs):
        assert kwargs["limit"] == 15
        assert kwargs["cursor"] == "cursor-1"
        assert kwargs["viewer_user_id"] is None
        return feed_page

    monkeypatch.setattr(feeds_module, "get_top_feed", fake_get_top_feed)

    with build_client(monkeypatch) as client:
        response = client.get("/v1/feeds/top?limit=15&cursor=cursor-1")

    assert response.status_code == 200
    body = response.json()
    assert body["page_info"] == {"next_cursor": "opaque-cursor", "has_next_page": True}
    assert body["items"][0]["title"] == "African startups are rethinking logistics infrastructure"
    assert "url_normalized" not in body["items"][0]
    assert "is_ingested" not in body["items"][0]


def test_top_feed_passes_viewer_context_when_authenticated(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_get_top_feed(**kwargs):
        assert kwargs["viewer_user_id"] == current_session.user.id
        assert kwargs["viewer_role"] == current_session.user.role
        return FeedPage(items=[make_post_read(viewer_vote=1)], page_info=PageInfo(next_cursor=None, has_next_page=False))

    monkeypatch.setattr(feeds_module, "get_top_feed", fake_get_top_feed)

    with build_client(monkeypatch, current_session=current_session) as client:
        response = client.get("/v1/feeds/top")

    assert response.status_code == 200
    assert response.json()["items"][0]["viewer_vote"] == 1


def test_jobs_feed_returns_expected_payload(monkeypatch) -> None:
    future_expiry = datetime.now(UTC)

    async def fake_get_jobs_feed(**_: object) -> FeedPage:
        return FeedPage(
            items=[make_post_read(job_expires_at=future_expiry)],
            page_info=PageInfo(next_cursor=None, has_next_page=False),
        )

    monkeypatch.setattr(feeds_module, "get_jobs_feed", fake_get_jobs_feed)

    with build_client(monkeypatch) as client:
        response = client.get("/v1/feeds/jobs")

    assert response.status_code == 200
    assert response.json()["items"][0]["post_type"] == "job"


def test_ask_feed_returns_expected_payload(monkeypatch) -> None:
    async def fake_get_ask_feed(**kwargs) -> FeedPage:
        assert kwargs["limit"] == 30
        return FeedPage(
            items=[make_category_post_read("ask")],
            page_info=PageInfo(next_cursor=None, has_next_page=False),
        )

    monkeypatch.setattr(feeds_module, "get_ask_feed", fake_get_ask_feed)

    with build_client(monkeypatch) as client:
        response = client.get("/v1/feeds/ask")

    assert response.status_code == 200
    assert response.json()["items"][0]["category"] == "ask"


def test_show_feed_returns_expected_payload(monkeypatch) -> None:
    async def fake_get_show_feed(**kwargs) -> FeedPage:
        assert kwargs["limit"] == 30
        return FeedPage(
            items=[make_category_post_read("show")],
            page_info=PageInfo(next_cursor=None, has_next_page=False),
        )

    monkeypatch.setattr(feeds_module, "get_show_feed", fake_get_show_feed)

    with build_client(monkeypatch) as client:
        response = client.get("/v1/feeds/show")

    assert response.status_code == 200
    assert response.json()["items"][0]["category"] == "show"


def test_post_detail_returns_expected_payload(monkeypatch) -> None:
    post_id = uuid4()

    async def fake_get_post_detail(**kwargs):
        assert kwargs["post_id"] == post_id
        return make_post_read(viewer_vote=1)

    monkeypatch.setattr(posts_module, "get_post_detail", fake_get_post_detail)

    with build_client(monkeypatch) as client:
        response = client.get(f"/v1/posts/{post_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["post"]["viewer_vote"] == 1
    assert "url_normalized" not in body["post"]
    assert "is_ingested" not in body["post"]


def test_post_detail_returns_not_found_for_missing_post(monkeypatch) -> None:
    async def fake_get_post_detail(**_: object):
        raise ReadError(404, "post_not_found", "The requested post does not exist.")

    monkeypatch.setattr(posts_module, "get_post_detail", fake_get_post_detail)

    with build_client(monkeypatch) as client:
        response = client.get(f"/v1/posts/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "post_not_found"


def test_post_comments_returns_flat_items(monkeypatch) -> None:
    parent = make_comment_read()
    child = make_comment_read(parent_comment_id=parent.id, depth=1)

    async def fake_get_post_comments(**kwargs):
        assert kwargs["sort"] == "new"
        return CommentPage(
            items=[parent, child],
            page_info=PageInfo(next_cursor=None, has_next_page=False),
        )

    monkeypatch.setattr(posts_module, "get_post_comments", fake_get_post_comments)

    with build_client(monkeypatch) as client:
        response = client.get(f"/v1/posts/{uuid4()}/comments?sort=new")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][1]["parent_comment_id"] == str(parent.id)
    assert body["items"][1]["depth"] == 1
    assert body["page_info"] == {"next_cursor": None, "has_next_page": False}


def test_post_comments_reject_invalid_sort(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.get(f"/v1/posts/{uuid4()}/comments?sort=bad")

    assert response.status_code == 422
