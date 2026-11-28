from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
import rifthub_backend.auth.service as service_module
from rifthub_backend.auth.security import hash_opaque_token, verify_password
from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserStatus

NEW_PASSWORD = "a-brand-new-password"


def make_settings() -> Settings:
    return Settings(environment="test", verification_delivery_mode="noop")


def make_user(*, status: UserStatus = UserStatus.ACTIVE) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        username="bheki",
        email="bheki@example.com",
        password_hash="old-hash",
        status=status,
    )


def make_token_row(*, expires_in_minutes: int = 30, used: bool = False) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        expires_at=now + timedelta(minutes=expires_in_minutes),
        consumed_at=now if used else None,
    )


def make_db(*scalar_results: object) -> SimpleNamespace:
    """A fake session whose scalar() returns the given values in order."""
    return SimpleNamespace(
        scalar=AsyncMock(side_effect=list(scalar_results)),
        add=Mock(),
        execute=AsyncMock(),
        commit=AsyncMock(),
    )


@pytest.mark.anyio
async def test_request_returns_email_whose_token_matches_the_stored_hash() -> None:
    db = make_db(make_user())

    email = await service_module.request_password_reset(
        db=db, settings=make_settings(), email=" Bheki@Example.com "
    )

    assert email is not None
    assert email.recipient_email == "bheki@example.com"
    raw_token = email.text.split("/reset-password?token=")[1].split()[0]
    stored = db.add.call_args.args[0]
    assert stored.token_hash == hash_opaque_token(raw_token)
    assert stored.token_hash != raw_token
    assert stored.expires_at - stored.created_at == timedelta(minutes=30)
    db.commit.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "user",
    [
        None,
        make_user(status=UserStatus.PENDING),
        make_user(status=UserStatus.SUSPENDED),
        make_user(status=UserStatus.BANNED),
    ],
)
async def test_request_sends_nothing_without_an_active_account(user) -> None:
    db = make_db(user)

    email = await service_module.request_password_reset(
        db=db, settings=make_settings(), email="bheki@example.com"
    )

    assert email is None
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_reset_saves_new_password_uses_token_and_deletes_sessions() -> None:
    user = make_user()
    token_row = make_token_row()
    db = make_db(user.id, user, token_row)

    await service_module.reset_password(
        db=db, settings=make_settings(), token="raw-token", new_password=NEW_PASSWORD
    )

    assert verify_password(NEW_PASSWORD, user.password_hash)
    assert token_row.consumed_at is not None
    assert "DELETE FROM user_sessions" in str(db.execute.await_args.args[0])
    db.commit.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("token_row", "expected_code"),
    [
        (make_token_row(used=True), "password_reset_token_invalid"),
        (make_token_row(expires_in_minutes=-1), "password_reset_token_expired"),
        (None, "password_reset_token_invalid"),
    ],
    ids=["already-used", "expired", "replaced-while-waiting"],
)
async def test_reset_rejects_an_unusable_token(token_row, expected_code) -> None:
    user = make_user()
    db = make_db(user.id, user, token_row)

    with pytest.raises(service_module.AuthError) as exc_info:
        await service_module.reset_password(
            db=db, settings=make_settings(), token="raw-token", new_password=NEW_PASSWORD
        )

    assert exc_info.value.code == expected_code
    assert user.password_hash == "old-hash"
    db.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_reset_rejects_unknown_token() -> None:
    db = make_db(None)

    with pytest.raises(service_module.AuthError) as exc_info:
        await service_module.reset_password(
            db=db, settings=make_settings(), token="nope", new_password=NEW_PASSWORD
        )

    assert exc_info.value.code == "password_reset_token_invalid"


@pytest.mark.anyio
async def test_reset_checks_password_before_touching_the_token() -> None:
    db = make_db()

    with pytest.raises(service_module.AuthError) as exc_info:
        await service_module.reset_password(
            db=db, settings=make_settings(), token="raw-token", new_password="short"
        )

    assert exc_info.value.code == "validation_error"
    db.scalar.assert_not_awaited()


@pytest.mark.anyio
async def test_login_fails_if_password_changed_while_it_was_being_checked(monkeypatch) -> None:
    db = make_db(make_user(), "hash-written-by-a-reset")
    monkeypatch.setattr(service_module, "verify_password", lambda *_: True)

    with pytest.raises(service_module.AuthError) as exc_info:
        await service_module.login_user(
            db=db, settings=make_settings(), email="bheki@example.com", password="old-password"
        )

    assert exc_info.value.code == "invalid_credentials"
    db.add.assert_not_called()


@pytest.mark.anyio
async def test_send_password_reset_email_does_not_raise_when_delivery_fails(monkeypatch) -> None:
    class FailingDelivery:
        async def send(self, email):
            raise RuntimeError("provider down")

    monkeypatch.setattr(service_module, "get_email_delivery", lambda settings: FailingDelivery())

    await service_module.send_password_reset_email(
        settings=make_settings(),
        email=SimpleNamespace(recipient_email="bheki@example.com"),
    )
