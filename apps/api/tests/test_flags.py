from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.auth.service import CurrentSession
from rifthub_backend.config import Settings
from rifthub_backend.db.types import FlagReason, FlagStatus, FlagTargetType, UserRole, UserStatus
from rifthub_backend.flags import FlaggingError

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.flags as flags_module


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
            created_at=now,
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


def make_flag():
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        target_type=FlagTargetType.COMMENT,
        target_id=uuid4(),
        reporter_id=uuid4(),
        reason_code=FlagReason.SPAM,
        notes="Looks bad.",
        status=FlagStatus.OPEN,
        reviewed_by_user_id=None,
        reviewed_at=None,
        created_at=now,
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


def test_create_flag_requires_auth(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post(
            "/v1/flags",
            json={
                "target_type": "comment",
                "target_id": str(uuid4()),
                "reason_code": "spam",
            },
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_create_flag_requires_valid_csrf(monkeypatch) -> None:
    current_session = make_current_session()

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/flags",
            json={
                "target_type": "comment",
                "target_id": str(uuid4()),
                "reason_code": "spam",
            },
            headers={"X-CSRF-Token": "wrong-csrf"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "CSRF validation failed."


def test_create_flag_returns_flag_shape(monkeypatch) -> None:
    current_session = make_current_session()
    fake_flag = make_flag()

    async def fake_create_flag(**kwargs):
        assert kwargs["reporter"] is current_session.user
        assert kwargs["payload"].target_type == FlagTargetType.COMMENT
        return fake_flag

    monkeypatch.setattr(flags_module, "create_flag", fake_create_flag)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/flags",
            json={
                "target_type": "comment",
                "target_id": str(fake_flag.target_id),
                "reason_code": "spam",
                "notes": "Looks duplicated.",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 201
    assert response.json()["flag"]["target_type"] == "comment"
    assert response.json()["flag"]["reason_code"] == "spam"
    assert response.json()["flag"]["status"] == "open"


def test_create_flag_duplicate_returns_409(monkeypatch) -> None:
    current_session = make_current_session()

    async def fake_create_flag(**_: object):
        raise FlaggingError(
            409,
            "duplicate_open_flag",
            "You have already reported this for the same reason.",
        )

    monkeypatch.setattr(flags_module, "create_flag", fake_create_flag)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            "/v1/flags",
            json={
                "target_type": "comment",
                "target_id": str(uuid4()),
                "reason_code": "spam",
            },
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_open_flag"
