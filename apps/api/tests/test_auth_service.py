from __future__ import annotations

import threading
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import rifthub_backend.auth.service as service_module
from rifthub_backend.auth.delivery import VerificationDeliveryResult
from rifthub_backend.config import Settings
from sqlalchemy.exc import IntegrityError


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


@pytest.mark.anyio
async def test_dispatch_verification_records_sent_status(monkeypatch) -> None:
    now = datetime.now(UTC)
    token_row = SimpleNamespace(
        delivery_status="pending",
        delivery_attempt_count=0,
        last_delivery_attempted_at=None,
        delivery_sent_at=None,
        delivery_failed_at=None,
        delivery_provider_message_id=None,
        delivery_error=None,
    )
    user = SimpleNamespace(email="bheki@example.com", username="bheki")
    db = AsyncMock()

    class FakeDelivery:
        async def send_verification(self, request):
            return VerificationDeliveryResult(provider_message_id="msg_123")

    monkeypatch.setattr(service_module, "get_verification_delivery", lambda settings: FakeDelivery())
    monkeypatch.setattr(service_module, "_utcnow", lambda: now)

    status = await service_module._dispatch_verification(
        db=db,
        token_row=token_row,
        settings=make_settings(),
        user=user,
        raw_token="verify-token",
        expires_at=now,
    )

    assert status == "sent"
    assert token_row.delivery_status == "sent"
    assert token_row.delivery_attempt_count == 1
    assert token_row.last_delivery_attempted_at == now
    assert token_row.delivery_sent_at == now
    assert token_row.delivery_failed_at is None
    assert token_row.delivery_provider_message_id == "msg_123"
    assert token_row.delivery_error is None
    db.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_dispatch_verification_records_failed_status(monkeypatch) -> None:
    now = datetime.now(UTC)
    token_row = SimpleNamespace(
        delivery_status="pending",
        delivery_attempt_count=0,
        last_delivery_attempted_at=None,
        delivery_sent_at=None,
        delivery_failed_at=None,
        delivery_provider_message_id=None,
        delivery_error=None,
    )
    user = SimpleNamespace(email="bheki@example.com", username="bheki")
    db = AsyncMock()

    class FakeDelivery:
        async def send_verification(self, request):
            raise RuntimeError("smtp down")

    monkeypatch.setattr(service_module, "get_verification_delivery", lambda settings: FakeDelivery())
    monkeypatch.setattr(service_module, "_utcnow", lambda: now)

    status = await service_module._dispatch_verification(
        db=db,
        token_row=token_row,
        settings=make_settings(),
        user=user,
        raw_token="verify-token",
        expires_at=now,
    )

    assert status == "failed"
    assert token_row.delivery_status == "failed"
    assert token_row.delivery_attempt_count == 1
    assert token_row.last_delivery_attempted_at == now
    assert token_row.delivery_sent_at is None
    assert token_row.delivery_failed_at == now
    assert token_row.delivery_provider_message_id is None
    assert token_row.delivery_error == "smtp down"
    db.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_login_hashes_password_off_the_event_loop_thread(monkeypatch) -> None:
    main_thread = threading.current_thread()
    seen_threads = []

    def fake_verify_password(raw_password: str, stored_hash: str) -> bool:
        seen_threads.append(threading.current_thread())
        return False

    async def fake_scalar(_statement):
        return SimpleNamespace(password_hash="stored-hash")

    monkeypatch.setattr(service_module, "verify_password", fake_verify_password)

    with pytest.raises(service_module.AuthError):
        await service_module.login_user(
            db=SimpleNamespace(scalar=fake_scalar),  # type: ignore[arg-type]
            settings=make_settings(),
            email="user@example.com",
            password="wrong-password",
        )

    assert seen_threads
    assert all(thread is not main_thread for thread in seen_threads)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("constraint_name", "expected_code"),
    [("uq_users_username", "duplicate_username"), ("uq_users_email", "duplicate_email")],
)
async def test_register_turns_a_duplicate_insert_race_into_409(
    constraint_name, expected_code
) -> None:
    async def no_existing_user(_statement):
        return None

    async def failing_flush() -> None:
        orig = SimpleNamespace(diag=SimpleNamespace(constraint_name=constraint_name))
        raise IntegrityError("INSERT INTO users", {}, orig)  # type: ignore[arg-type]

    db = SimpleNamespace(
        scalar=no_existing_user,
        add=lambda _row: None,
        flush=failing_flush,
        rollback=AsyncMock(),
    )

    with pytest.raises(service_module.AuthError) as exc_info:
        await service_module.register_user(
            db=db,  # type: ignore[arg-type]
            settings=make_settings(),
            username="avery",
            email="avery@example.com",
            password="a-strong-password-123",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == expected_code
    db.rollback.assert_awaited_once()
