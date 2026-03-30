from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.auth.service import CurrentSession
from rifthub_backend.config import Settings
from rifthub_backend.creation import CreationError
from rifthub_backend.db.types import CommentStatus, PostStatus, PostType, UserRole, UserStatus
from rifthub_backend.reads import CommentRead, DomainSummary, PostRead, UserSummary

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
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


def make_current_session(*, status: UserStatus = UserStatus.ACTIVE) -> CurrentSession:
    user_id = uuid4()
    return CurrentSession(
        user=SimpleNamespace(
            id=user_id,
            username="bheki",
            role=UserRole.USER,
            status=status,
        ),
        session=SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            session_token_hash="session-hash",
            expires_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        ),
        csrf_token="csrf-token",
    )


def make_post_read(*, post_type: PostType = PostType.TEXT, body_markdown: str | None = "Body", url: str | None = None) -> PostRead:
    now = datetime.now(UTC)
    return PostRead(
        id=uuid4(),
        title="A post",
        slug="a-post",
        post_type=post_type,
        category="ask" if post_type == PostType.TEXT else "jobs" if post_type == PostType.JOB else "ecosystem",
        status=PostStatus.ACTIVE,
        url=url,
        body_markdown=body_markdown,
        author=UserSummary(id=uuid4(), username="bheki"),
        domain=DomainSummary(id=uuid4(), hostname="example.com", display_name="Example") if url else None,
        upvote_count=0,
        downvote_count=0,
        comment_count=0,
        score=0,
        rank_score=0.0,
        viewer_vote=None,
        viewer_can_edit=True,
        viewer_can_moderate=False,
        submitted_at=now,
        created_at=now,
        updated_at=now,
        last_commented_at=None,
        job_expires_at=None,
    )


def make_comment_read(*, parent_comment_id=None, depth: int = 0) -> CommentRead:
    now = datetime.now(UTC)
    return CommentRead(
        id=uuid4(),
        post_id=uuid4(),
        parent_comment_id=parent_comment_id,
        depth=depth,
        body_markdown="Comment body",
        status=CommentStatus.ACTIVE,
        author=UserSummary(id=uuid4(), username="bheki"),
        upvote_count=0,
        downvote_count=0,
        score=0,
        rank_score=0.0,
        viewer_vote=None,
        viewer_can_edit=True,
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


def _set_auth_cookies(client: TestClient) -> None:
    client.cookies.set("rifthub_session", "raw-session-token")
    client.cookies.set("rifthub_csrf", "csrf-token")


def test_create_text_post_requires_auth(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "text",
                "category": "ask",
                "title": "A text post",
                "body_markdown": "Body",
            },
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_text_post_requires_valid_csrf(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "text",
                "category": "ask",
                "title": "A text post",
                "body_markdown": "Body",
            },
            headers={"X-CSRF-Token": "wrong-csrf"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "CSRF validation failed."


def test_create_text_post_returns_post_shape(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_post(**kwargs):
        assert kwargs["author"] is current_session.user
        assert kwargs["payload"].post_type == PostType.TEXT
        return make_post_read(post_type=PostType.TEXT, body_markdown="Body")

    monkeypatch.setattr(posts_module, "create_post", fake_create_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "text",
                "category": "ask",
                "title": "A text post",
                "body_markdown": "Body",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 201
    assert response.json()["post"]["post_type"] == "text"
    assert response.json()["post"]["viewer_can_edit"] is True


def test_create_link_post_duplicate_returns_409(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_post(**_: object):
        raise CreationError(
            409,
            "duplicate_submission",
            "This story has already been submitted recently.",
            details={"existing_post_id": str(uuid4()), "existing_post_slug": "existing-post"},
        )

    monkeypatch.setattr(posts_module, "create_post", fake_create_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "link",
                "category": "ecosystem",
                "title": "A link post",
                "url": "https://example.com/story",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_submission"


def test_create_job_post_with_body_only(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_post(**kwargs):
        assert kwargs["payload"].job_expires_at is not None
        return make_post_read(post_type=PostType.JOB, body_markdown="Remote-friendly role", url=None)

    monkeypatch.setattr(posts_module, "create_post", fake_create_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "job",
                "category": "jobs",
                "title": "Senior Backend Engineer",
                "body_markdown": "Remote-friendly role",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 201
    assert response.json()["post"]["post_type"] == "job"
    assert response.json()["post"]["url"] is None


def test_create_non_job_post_rejects_job_expiry(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "text",
                "category": "ask",
                "title": "A text post",
                "body_markdown": "Body",
                "job_expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_job_post_rejects_expiry_beyond_thirty_days(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "job",
                "category": "jobs",
                "title": "Senior Backend Engineer",
                "body_markdown": "Remote-friendly role",
                "job_expires_at": (datetime.now(UTC) + timedelta(days=31)).isoformat(),
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_post_returns_403_for_suspended_user(monkeypatch) -> None:
    current_session = make_current_session(status=UserStatus.SUSPENDED)

    async def fake_create_post(**_: object):
        raise CreationError(403, "forbidden", "Your account cannot perform this action.")

    monkeypatch.setattr(posts_module, "create_post", fake_create_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/posts",
            json={
                "post_type": "text",
                "category": "ask",
                "title": "A text post",
                "body_markdown": "Body",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_create_comment_requires_auth(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A comment"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_comment_returns_comment_shape(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_comment(**kwargs):
        assert kwargs["author"] is current_session.user
        assert kwargs["payload"].body_markdown == "A comment"
        return make_comment_read()

    monkeypatch.setattr(posts_module, "create_comment", fake_create_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A comment"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 201
    assert response.json()["comment"]["body_markdown"] == "Comment body"


def test_create_comment_reply_returns_depth(monkeypatch) -> None:
    current_session = make_current_session()
    parent_id = uuid4()

    async def fake_create_comment(**kwargs):
        assert kwargs["payload"].parent_comment_id == parent_id
        return make_comment_read(parent_comment_id=parent_id, depth=1)

    monkeypatch.setattr(posts_module, "create_comment", fake_create_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A reply", "parent_comment_id": str(parent_id)},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 201
    assert response.json()["comment"]["depth"] == 1


def test_create_comment_parent_not_found_returns_404(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_comment(**_: object):
        raise CreationError(404, "comment_not_found", "The requested comment does not exist.")

    monkeypatch.setattr(posts_module, "create_comment", fake_create_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A reply", "parent_comment_id": str(uuid4())},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "comment_not_found"


def test_create_comment_depth_overflow_returns_422(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_comment(**_: object):
        raise CreationError(422, "validation_error", "Comment depth exceeds the allowed maximum.")

    monkeypatch.setattr(posts_module, "create_comment", fake_create_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A deep reply", "parent_comment_id": str(uuid4())},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_comment_returns_403_for_banned_user(monkeypatch) -> None:
    current_session = make_current_session(status=UserStatus.BANNED)

    async def fake_create_comment(**_: object):
        raise CreationError(403, "forbidden", "Your account cannot perform this action.")

    monkeypatch.setattr(posts_module, "create_comment", fake_create_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/comments",
            json={"body_markdown": "A comment"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
