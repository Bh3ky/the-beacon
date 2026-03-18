from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserRole, UserStatus
from rifthub_backend.auth.service import CurrentSession, PendingRegistration, SessionAuthResult

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.auth as auth_module


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


def make_user(*, status: UserStatus = UserStatus.ACTIVE) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        username="bheki",
        email="bheki@example.com",
        password_hash="stored-hash",
        bio=None,
        role=UserRole.USER,
        status=status,
        karma=0,
        post_count=0,
        comment_count=0,
        avatar_url=None,
        created_at=now,
        updated_at=now,
        last_active_at=now,
    )


def make_session_result() -> SessionAuthResult:
    user = make_user()
    session = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        session_token_hash="session-hash",
        expires_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )
    return SessionAuthResult(
        user=user,
        session=session,
        raw_session_token="raw-session-token",
        csrf_token="csrf-token",
    )


def build_client(monkeypatch, *, settings: Settings | None = None) -> TestClient:
    app_settings = settings or make_settings()
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

    async def allow_rate_limit(**_: object) -> None:
        return None

    monkeypatch.setattr(auth_module.rate_limiter, "check", allow_rate_limit)

    app = main_module.create_app()
    app.dependency_overrides[dependencies_module.get_db_session] = fake_get_db_session
    app.dependency_overrides[dependencies_module.get_settings] = lambda: app_settings
    return TestClient(app)


def test_register_returns_pending_user_without_session_cookie(monkeypatch) -> None:
    pending_user = make_user(status=UserStatus.PENDING)

    async def fake_register_user(**_: object) -> PendingRegistration:
        return PendingRegistration(user=pending_user)

    monkeypatch.setattr(auth_module, "register_user", fake_register_user)

    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/auth/register",
            json={
                "username": "bheki",
                "email": "bheki@example.com",
                "password": "avery-strong-password",
            },
        )

    assert response.status_code == 201
    assert response.json()["verification_required"] is True
    assert response.json()["user"]["status"] == "pending"
    assert "set-cookie" not in response.headers


def test_resend_verification_returns_no_content(monkeypatch) -> None:
    async def fake_resend_verification(**_: object) -> None:
        return None

    monkeypatch.setattr(auth_module, "resend_verification_email", fake_resend_verification)

    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/auth/resend-verification",
            json={"email": "bheki@example.com"},
        )

    assert response.status_code == 204


def test_verify_sets_auth_and_csrf_cookies(monkeypatch) -> None:
    async def fake_verify_account(**_: object) -> SessionAuthResult:
        return make_session_result()

    monkeypatch.setattr(auth_module, "verify_account", fake_verify_account)

    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/verify", json={"token": "verify-token"})

    assert response.status_code == 200
    set_cookie = " ".join(response.headers.get_list("set-cookie"))
    assert "rifthub_session=raw-session-token" in set_cookie
    assert "rifthub_csrf=csrf-token" in set_cookie


def test_login_sets_auth_and_csrf_cookies(monkeypatch) -> None:
    async def fake_login_user(**_: object) -> SessionAuthResult:
        return make_session_result()

    monkeypatch.setattr(auth_module, "login_user", fake_login_user)

    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/auth/login",
            json={
                "email": "bheki@example.com",
                "password": "avery-strong-password",
            },
        )

    assert response.status_code == 200
    set_cookie = " ".join(response.headers.get_list("set-cookie"))
    assert "rifthub_session=raw-session-token" in set_cookie
    assert "rifthub_csrf=csrf-token" in set_cookie


def test_logout_is_idempotent_without_session(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/logout")

    assert response.status_code == 204


def test_logout_requires_csrf_when_session_exists(monkeypatch) -> None:
    current_user = make_user()
    current_session = CurrentSession(
        user=current_user,
        session=SimpleNamespace(
            id=uuid4(),
            user_id=current_user.id,
            session_token_hash="session-hash",
            expires_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        ),
        csrf_token="expected-csrf",
    )

    async def fake_get_current_session() -> CurrentSession:
        return current_session

    async def fake_logout_session(**_: object) -> None:
        return None

    monkeypatch.setattr(auth_module, "logout_session", fake_logout_session)

    with build_client(monkeypatch) as client:
        client.cookies.set("rifthub_session", "raw-session-token")
        client.cookies.set("rifthub_csrf", "wrong-csrf")
        client.app.dependency_overrides[dependencies_module.get_current_session] = fake_get_current_session
        response = client.post(
            "/v1/auth/logout",
            headers={"X-CSRF-Token": "wrong-csrf"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "CSRF validation failed."


def test_me_returns_authenticated_user_and_refreshes_missing_csrf_cookie(monkeypatch) -> None:
    current_user = make_user()
    current_session = CurrentSession(
        user=current_user,
        session=SimpleNamespace(
            id=uuid4(),
            user_id=current_user.id,
            session_token_hash="session-hash",
            expires_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        ),
        csrf_token="fresh-csrf-token",
    )

    async def fake_get_current_session() -> CurrentSession:
        return current_session

    with build_client(monkeypatch) as client:
        client.cookies.set("rifthub_session", "raw-session-token")
        client.app.dependency_overrides[dependencies_module.get_current_session] = fake_get_current_session
        response = client.get("/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "bheki"
    assert "rifthub_csrf=fresh-csrf-token" in " ".join(response.headers.get_list("set-cookie"))


def test_mutating_route_rejects_disallowed_origin(monkeypatch) -> None:
    async def fake_register_user(**_: object) -> PendingRegistration:
        return PendingRegistration(user=make_user(status=UserStatus.PENDING))

    monkeypatch.setattr(auth_module, "register_user", fake_register_user)

    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/auth/register",
            json={
                "username": "bheki",
                "email": "bheki@example.com",
                "password": "avery-strong-password",
            },
            headers={"Origin": "https://evil.example"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Origin is not allowed."
