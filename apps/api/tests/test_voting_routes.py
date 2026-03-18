from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.auth.service import CurrentSession
from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserRole, UserStatus
from rifthub_backend.voting import CommentVoteRead, PostVoteRead, VotingError

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.comments as comments_module
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
    now = datetime.now(UTC)
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
            expires_at=now,
            created_at=now,
            last_seen_at=now,
        ),
        csrf_token="csrf-token",
    )


def make_post_vote_read(*, viewer_vote: int | None = 1, score: int = 19) -> PostVoteRead:
    return PostVoteRead(
        id=uuid4(),
        upvote_count=19 if viewer_vote is not None else 18,
        downvote_count=0,
        score=score,
        rank_score=6.0142 if viewer_vote is not None else 5.9142,
        viewer_vote=viewer_vote,
    )


def make_comment_vote_read(*, viewer_vote: int | None = 1, score: int = 6) -> CommentVoteRead:
    return CommentVoteRead(
        id=uuid4(),
        upvote_count=6 if viewer_vote is not None else 5,
        downvote_count=0,
        score=score,
        rank_score=float(score),
        viewer_vote=viewer_vote,
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


def test_create_post_vote_requires_auth(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 1},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_post_vote_requires_valid_csrf(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "wrong-csrf"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "CSRF validation failed."


def test_create_post_vote_returns_minimal_payload(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_vote_on_post(**kwargs):
        assert kwargs["user"] is current_session.user
        assert kwargs["vote_value"] == 1
        return make_post_vote_read(viewer_vote=1)

    monkeypatch.setattr(posts_module, "vote_on_post", fake_vote_on_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["post"]["viewer_vote"] == 1
    assert "title" not in response.json()["post"]


def test_create_post_vote_allows_downvote_payload(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_vote_on_post(**kwargs):
        assert kwargs["vote_value"] == -1
        return make_post_vote_read(viewer_vote=-1, score=17)

    monkeypatch.setattr(posts_module, "vote_on_post", fake_vote_on_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": -1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["post"]["viewer_vote"] == -1


def test_create_post_vote_returns_403_for_suspended_user(monkeypatch) -> None:
    current_session = make_current_session(status=UserStatus.SUSPENDED)

    async def fake_vote_on_post(**_: object):
        raise VotingError(403, "forbidden", "Your account cannot perform this action.")

    monkeypatch.setattr(posts_module, "vote_on_post", fake_vote_on_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_create_post_vote_rejects_invalid_value(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 0},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_post_vote_returns_404_for_missing_post(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_vote_on_post(**_: object):
        raise VotingError(404, "post_not_found", "The requested post does not exist.")

    monkeypatch.setattr(posts_module, "vote_on_post", fake_vote_on_post)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/posts/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "post_not_found"


def test_delete_post_vote_returns_cleared_viewer_vote(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_remove_post_vote(**kwargs):
        assert kwargs["user"] is current_session.user
        return make_post_vote_read(viewer_vote=None, score=18)

    monkeypatch.setattr(posts_module, "remove_post_vote", fake_remove_post_vote)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.delete(
            f"/v1/posts/{uuid4()}/vote",
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["post"]["viewer_vote"] is None


def test_delete_missing_post_vote_still_succeeds(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_remove_post_vote(**_: object):
        return make_post_vote_read(viewer_vote=None, score=18)

    monkeypatch.setattr(posts_module, "remove_post_vote", fake_remove_post_vote)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.delete(
            f"/v1/posts/{uuid4()}/vote",
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["post"]["viewer_vote"] is None


def test_create_comment_vote_returns_minimal_payload(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_vote_on_comment(**kwargs):
        assert kwargs["user"] is current_session.user
        assert kwargs["vote_value"] == 1
        return make_comment_vote_read(viewer_vote=1)

    monkeypatch.setattr(comments_module, "vote_on_comment", fake_vote_on_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/comments/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["comment"]["viewer_vote"] == 1
    assert "body_markdown" not in response.json()["comment"]


def test_create_comment_vote_requires_auth(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post(
            f"/v1/comments/{uuid4()}/vote",
            json={"vote_value": 1},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_comment_vote_returns_403_for_banned_user(monkeypatch) -> None:
    current_session = make_current_session(status=UserStatus.BANNED)

    async def fake_vote_on_comment(**_: object):
        raise VotingError(403, "forbidden", "Your account cannot perform this action.")

    monkeypatch.setattr(comments_module, "vote_on_comment", fake_vote_on_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/comments/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_create_comment_vote_rejects_invalid_value(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/comments/{uuid4()}/vote",
            json={"vote_value": 0},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_comment_vote_returns_404_for_missing_comment(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_vote_on_comment(**_: object):
        raise VotingError(404, "comment_not_found", "The requested comment does not exist.")

    monkeypatch.setattr(comments_module, "vote_on_comment", fake_vote_on_comment)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/comments/{uuid4()}/vote",
            json={"vote_value": 1},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "comment_not_found"


def test_delete_comment_vote_returns_cleared_viewer_vote(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_remove_comment_vote(**kwargs):
        assert kwargs["user"] is current_session.user
        return make_comment_vote_read(viewer_vote=None, score=5)

    monkeypatch.setattr(comments_module, "remove_comment_vote", fake_remove_comment_vote)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.delete(
            f"/v1/comments/{uuid4()}/vote",
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["comment"]["viewer_vote"] is None


def test_delete_missing_comment_vote_still_succeeds(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_remove_comment_vote(**_: object):
        return make_comment_vote_read(viewer_vote=None, score=5)

    monkeypatch.setattr(comments_module, "remove_comment_vote", fake_remove_comment_vote)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.delete(
            f"/v1/comments/{uuid4()}/vote",
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["comment"]["viewer_vote"] is None
