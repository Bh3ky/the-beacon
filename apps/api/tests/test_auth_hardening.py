from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from starlette.requests import Request

from rifthub_backend.auth.service import AuthError, CurrentSession, SessionAuthResult
from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserRole, UserStatus
from rifthub_api.errors import ApiError

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


def make_session_result(*, raw_session_token: str = "raw-session-token") -> SessionAuthResult:
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
        raw_session_token=raw_session_token,
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


def test_verify_rejects_expired_token(monkeypatch) -> None:
    async def fake_verify_account(**_: object):
        raise AuthError(400, "verification_token_expired", "Verification token has expired.")

    monkeypatch.setattr(auth_module, "verify_account", fake_verify_account)

    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/verify", json={"token": "expired-token"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "verification_token_expired"


def test_verify_rejects_garbage_token(monkeypatch) -> None:
    async def fake_verify_account(**_: object):
        raise AuthError(400, "verification_token_invalid", "Verification token is invalid.")

    monkeypatch.setattr(auth_module, "verify_account", fake_verify_account)

    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/verify", json={"token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "verification_token_invalid"


def test_verify_rejects_reused_token(monkeypatch) -> None:
    async def fake_verify_account(**_: object):
        raise AuthError(409, "conflict", "Account is already verified.")

    monkeypatch.setattr(auth_module, "verify_account", fake_verify_account)

    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/verify", json={"token": "used-token"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_resend_verification_remains_no_content_after_verification(monkeypatch) -> None:
    async def fake_resend_verification(**_: object) -> None:
        return None

    monkeypatch.setattr(auth_module, "resend_verification_email", fake_resend_verification)

    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/auth/resend-verification",
            json={"email": "bheki@example.com"},
        )

    assert response.status_code == 204


def test_login_unknown_email_and_wrong_password_share_same_error_contract(monkeypatch) -> None:
    async def fake_login_user(**_: object):
        raise AuthError(401, "invalid_credentials", "Invalid credentials.")

    monkeypatch.setattr(auth_module, "login_user", fake_login_user)

    with build_client(monkeypatch) as client:
        unknown_email = client.post(
            "/v1/auth/login",
            json={"email": "doesnotexist@example.com", "password": "anything"},
        )
        wrong_password = client.post(
            "/v1/auth/login",
            json={"email": "bheki@example.com", "password": "wrong-password"},
        )

    assert unknown_email.status_code == 401
    assert wrong_password.status_code == 401
    assert unknown_email.json()["error"] == wrong_password.json()["error"]


def test_login_returns_rate_limited_when_limiter_blocks(monkeypatch) -> None:
    async def block_rate_limit(**_: object) -> None:
        raise ApiError(
            status_code=429,
            code="rate_limited",
            message="Too many login attempts. Try again later.",
        )

    with build_client(monkeypatch) as client:
        monkeypatch.setattr(auth_module.rate_limiter, "check", block_rate_limit)
        response = client.post(
            "/v1/auth/login",
            json={"email": "bheki@example.com", "password": "avery-strong-password"},
        )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"


def test_old_session_cookie_is_rejected_after_logout(monkeypatch) -> None:
    session_before_logout = make_session_result(raw_session_token="old-session-token")
    current_user = session_before_logout.user
    current_session = CurrentSession(
        user=current_user,
        session=session_before_logout.session,
        csrf_token="csrf-token",
    )

    async def fake_get_current_session() -> CurrentSession:
        return current_session

    async def fake_logout_session(**_: object) -> None:
        return None

    async def fake_current_session_after_logout():
        return None

    with build_client(monkeypatch) as client:
        monkeypatch.setattr(auth_module, "logout_session", fake_logout_session)
        client.cookies.set("rifthub_session", "old-session-token")
        client.cookies.set("rifthub_csrf", "csrf-token")
        client.app.dependency_overrides[dependencies_module.get_current_session] = fake_get_current_session

        logout_response = client.post(
            "/v1/auth/logout",
            headers={"X-CSRF-Token": "csrf-token"},
        )

        assert logout_response.status_code == 204

        client.cookies.set("rifthub_session", "old-session-token")
        client.app.dependency_overrides[dependencies_module.get_current_session] = fake_current_session_after_logout
        me_response = client.get("/v1/auth/me")

    assert me_response.status_code == 401
    assert me_response.json()["error"]["code"] == "unauthenticated"


def make_request(*, client_host: str, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/auth/login",
        "headers": raw_headers,
        "client": (client_host, 12345),
    }
    return Request(scope)


def test_client_ip_prefers_forwarded_for_from_trusted_proxy() -> None:
    settings = make_settings()
    request = make_request(
        client_host="127.0.0.1",
        headers={"x-forwarded-for": "203.0.113.9, 127.0.0.1"},
    )

    assert auth_module._client_ip(request, settings) == "203.0.113.9"


def test_client_ip_ignores_forwarded_for_from_untrusted_proxy() -> None:
    settings = Settings(
        **{
            **make_settings().__dict__,
            "trusted_proxy_ips": (),
        }
    )
    request = make_request(
        client_host="198.51.100.20",
        headers={"x-forwarded-for": "203.0.113.9"},
    )

    assert auth_module._client_ip(request, settings) == "198.51.100.20"
