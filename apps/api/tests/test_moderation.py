from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from rifthub_backend.auth.service import CurrentSession
from rifthub_backend.config import Settings
from rifthub_backend.db.types import (
    FlagReason,
    FlagStatus,
    FlagTargetType,
    ModerationActionType,
    ModerationTargetType,
    UserRole,
    UserStatus,
)
from rifthub_backend.moderation import ModerationError

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.moderation as moderation_module


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


def make_current_session(
    *,
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
) -> CurrentSession:
    user_id = uuid4()
    now = datetime.now(UTC)
    return CurrentSession(
        user=SimpleNamespace(
            id=user_id,
            username="moderator1",
            role=role,
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


def make_flag(*, target_type: FlagTargetType = FlagTargetType.COMMENT):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        target_type=target_type,
        target_id=uuid4(),
        reporter_id=uuid4(),
        reason_code=FlagReason.SPAM,
        notes="Looks bad.",
        status=FlagStatus.OPEN,
        reviewed_by_user_id=None,
        reviewed_at=None,
        created_at=now,
    )


def make_queue_item():
    flag = make_flag(target_type=FlagTargetType.POST)
    return SimpleNamespace(
        flag=flag,
        reporter=SimpleNamespace(id=uuid4(), username="reporter1"),
        target=SimpleNamespace(
            id=flag.target_id,
            target_type=FlagTargetType.POST,
            title="Suspicious launch post",
            excerpt="promo-heavy body",
            username="founder1",
            status="active",
        ),
    )


def make_action_result(*, action_type: ModerationActionType):
    now = datetime.now(UTC)
    flag = make_flag(
        target_type=(
            FlagTargetType.USER
            if action_type in {ModerationActionType.SUSPEND_USER, ModerationActionType.BAN_USER}
            else FlagTargetType.POST
        )
    )
    target_id = flag.target_id
    action_target_type = ModerationTargetType.POST
    if action_type in {ModerationActionType.SUSPEND_USER, ModerationActionType.BAN_USER}:
        action_target_type = ModerationTargetType.USER
    if action_type in {ModerationActionType.APPROVE_INGESTION, ModerationActionType.REJECT_INGESTION}:
        action_target_type = ModerationTargetType.INGESTION_ITEM
    return SimpleNamespace(
        action=SimpleNamespace(
            id=uuid4(),
            moderator_id=uuid4(),
            target_type=action_target_type,
            target_id=target_id,
            action_type=action_type,
            reason="policy violation",
            metadata_json={"flag_id": str(flag.id)},
            created_at=now,
            updated_at=now,
        ),
        flag=SimpleNamespace(
            id=flag.id,
            target_type=flag.target_type,
            target_id=flag.target_id,
            reporter_id=flag.reporter_id,
            reason_code=flag.reason_code,
            notes=flag.notes,
            status=FlagStatus.RESOLVED,
            reviewed_by_user_id=uuid4(),
            reviewed_at=now,
            created_at=flag.created_at,
        ),
    )


def make_ingestion_queue_item():
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        title="Startup raises seed funding",
        url="https://example.com/story-1",
        ingestion_status="awaiting_review",
        detected_category="funding",
        published_at_external=now,
        discovered_at=now,
        processing_notes="Awaiting manual ingestion review.",
        source=SimpleNamespace(
            id=uuid4(),
            name="TechCabal",
            source_type="rss",
            status="active",
            auto_publish=False,
        ),
        linked_post_id=None,
        dedupe_match_post_id=None,
    )


def make_source_health_item():
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        name="Disrupt Africa",
        source_type="rss",
        status="active",
        auto_publish=False,
        poll_interval_minutes=30,
        last_checked_at=now,
        last_success_at=None,
        last_error_at=now,
        last_error_message="HTTP 500",
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
    app.dependency_overrides[dependencies_module.get_current_session] = lambda: current_session
    return TestClient(app)


def _set_auth_cookies(client: TestClient) -> None:
    client.cookies.set("rifthub_session", "session-token")
    client.cookies.set("rifthub_csrf", "csrf-token")


def test_list_open_flags_requires_authentication(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.get("/v1/moderation/flags")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_list_open_flags_requires_moderator_role(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.USER)

    with build_client(monkeypatch, current_session=current_session) as client:
        response = client.get("/v1/moderation/flags")

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Moderator access is required."


def test_list_open_flags_returns_queue_items_for_moderator(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)
    queue_item = make_queue_item()

    async def fake_list_open_flags(**kwargs):
        assert kwargs["limit"] == 25
        return [queue_item]

    monkeypatch.setattr(moderation_module, "list_open_flags", fake_list_open_flags)

    with build_client(monkeypatch, current_session=current_session) as client:
        response = client.get("/v1/moderation/flags?limit=25")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["flag"]["target_type"] == "post"
    assert payload["items"][0]["reporter"]["username"] == "reporter1"
    assert payload["items"][0]["target"]["title"] == "Suspicious launch post"


def test_list_ingestion_review_items_returns_queue_items_for_moderator(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)
    queue_item = make_ingestion_queue_item()

    async def fake_list_ingestion_review_items(**kwargs):
        assert kwargs["limit"] == 10
        return [queue_item]

    monkeypatch.setattr(moderation_module, "list_ingestion_review_items", fake_list_ingestion_review_items)

    with build_client(monkeypatch, current_session=current_session) as client:
        response = client.get("/v1/moderation/ingestion/items?limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["title"] == "Startup raises seed funding"
    assert payload["items"][0]["source"]["name"] == "TechCabal"


def test_list_source_health_returns_items_for_moderator(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)
    source_item = make_source_health_item()

    async def fake_list_source_health(**kwargs):
        assert kwargs["limit"] == 5
        assert kwargs["failures_only"] is True
        return [source_item]

    monkeypatch.setattr(moderation_module, "list_source_health", fake_list_source_health)

    with build_client(monkeypatch, current_session=current_session) as client:
        response = client.get("/v1/moderation/ingestion/sources?limit=5&failures_only=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == "Disrupt Africa"
    assert payload["items"][0]["last_error_message"] == "HTTP 500"


def test_dismiss_flag_requires_valid_csrf(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(f"/v1/moderation/flags/{uuid4()}/dismiss", headers={"X-CSRF-Token": "wrong"})

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "CSRF validation failed."


def test_dismiss_flag_returns_updated_flag(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)
    fake_flag = make_flag(target_type=FlagTargetType.COMMENT)
    now = datetime.now(UTC)
    fake_flag.status = FlagStatus.DISMISSED
    fake_flag.reviewed_by_user_id = current_session.user.id
    fake_flag.reviewed_at = now

    async def fake_dismiss_flag(**kwargs):
        assert kwargs["moderator"] is current_session.user
        return fake_flag

    monkeypatch.setattr(moderation_module, "dismiss_flag", fake_dismiss_flag)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/flags/{fake_flag.id}/dismiss",
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    assert response.json()["flag"]["status"] == "dismissed"


def test_suspend_user_returns_moderation_action(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)
    result = make_action_result(action_type=ModerationActionType.SUSPEND_USER)

    async def fake_suspend_user(**kwargs):
        assert kwargs["moderator"] is current_session.user
        assert kwargs["payload"].reason == "spam wave"
        return result

    monkeypatch.setattr(moderation_module, "suspend_user", fake_suspend_user)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/users/{result.action.target_id}/suspend",
            json={"reason": "spam wave", "flag_id": str(result.flag.id)},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"]["action_type"] == "suspend_user"
    assert payload["flag"]["status"] == "resolved"


def test_ban_user_requires_admin_role(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/users/{uuid4()}/ban",
            json={"reason": "severe abuse"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Administrator access is required."


def test_ban_user_returns_structured_error(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.ADMIN)

    async def fake_ban_user(**_: object):
        raise ModerationError(409, "user_already_banned", "The user is already banned.")

    monkeypatch.setattr(moderation_module, "ban_user", fake_ban_user)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/users/{uuid4()}/ban",
            json={"reason": "repeat abuse"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "user_already_banned"


def test_approve_ingestion_item_returns_moderation_action(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.ADMIN)
    result = make_action_result(action_type=ModerationActionType.APPROVE_INGESTION)
    result.action.target_id = uuid4()
    result.flag = None

    async def fake_approve_ingestion_item(**kwargs):
        assert kwargs["moderator"] is current_session.user
        assert kwargs["payload"].reason == "trusted source"
        return result

    monkeypatch.setattr(moderation_module, "approve_ingestion_item", fake_approve_ingestion_item)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/ingestion/items/{result.action.target_id}/approve",
            json={"reason": "trusted source"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"]["action_type"] == "approve_ingestion"
    assert payload["action"]["target_type"] == "ingestion_item"
    assert payload["flag"] is None


def test_reject_ingestion_item_returns_structured_error(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.ADMIN)

    async def fake_reject_ingestion_item(**_: object):
        raise ModerationError(
            409,
            "ingestion_item_not_awaiting_review",
            "The ingestion item is not awaiting review.",
        )

    monkeypatch.setattr(moderation_module, "reject_ingestion_item", fake_reject_ingestion_item)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/ingestion/items/{uuid4()}/reject",
            json={"reason": "off scope"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ingestion_item_not_awaiting_review"


def test_ingestion_review_actions_require_admin_role(monkeypatch) -> None:
    current_session = make_current_session(role=UserRole.MODERATOR)

    with build_client(monkeypatch, current_session=current_session) as client:
        _set_auth_cookies(client)
        response = client.post(
            f"/v1/moderation/ingestion/items/{uuid4()}/approve",
            json={"reason": "trusted source"},
            headers={"X-CSRF-Token": "csrf-token"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Administrator access is required."
