from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.auth as auth_module
from fastapi.testclient import TestClient
from rifthub_backend.auth.delivery import OutgoingEmail
from rifthub_backend.auth.service import AuthError
from rifthub_backend.config import Settings

REQUEST_URL = "/v1/auth/password-reset/request"
CONFIRM_URL = "/v1/auth/password-reset/confirm"


@pytest.fixture
def client(monkeypatch):
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        verification_delivery_mode="noop",
    )
    fake_engine = object()

    async def fake_ping_database(_engine: object) -> None:
        return None

    async def fake_dispose_engine() -> None:
        return None

    async def fake_get_db_session() -> AsyncIterator[object]:
        yield object()

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: fake_engine)
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_dispose_engine)

    app = main_module.create_app()
    app.dependency_overrides[dependencies_module.get_db_session] = fake_get_db_session
    app.dependency_overrides[dependencies_module.get_settings] = lambda: settings
    # Leaving the block shuts the app down, which also clears the rate limit counters.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sent(monkeypatch) -> list[OutgoingEmail]:
    """Only "known@example.com" has an account. Collects the emails sent."""
    emails: list[OutgoingEmail] = []

    async def fake_request_password_reset(*, email: str, **_: object) -> OutgoingEmail | None:
        if email != "known@example.com":
            return None
        return OutgoingEmail(recipient_email=email, subject="Reset", text="link")

    async def fake_send_password_reset_email(*, email: OutgoingEmail, **_: object) -> None:
        emails.append(email)

    monkeypatch.setattr(auth_module, "request_password_reset", fake_request_password_reset)
    monkeypatch.setattr(auth_module, "send_password_reset_email", fake_send_password_reset_email)
    return emails


def test_request_looks_the_same_for_known_and_unknown_emails(client, sent) -> None:
    known = client.post(REQUEST_URL, json={"email": "known@example.com"})
    unknown = client.post(REQUEST_URL, json={"email": "unknown@example.com"})

    assert (known.status_code, known.content) == (204, b"")
    assert (unknown.status_code, unknown.content) == (204, b"")
    assert [email.recipient_email for email in sent] == ["known@example.com"]


def test_request_is_limited_per_ip(client, sent) -> None:
    codes = [
        client.post(REQUEST_URL, json={"email": f"person{number}@example.com"}).status_code
        for number in range(4)
    ]

    assert codes == [204, 204, 204, 429]


def test_request_is_limited_per_email_across_ips(client, sent, monkeypatch) -> None:
    ips = iter(["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"])
    monkeypatch.setattr(auth_module, "_client_ip", lambda *_: next(ips))

    codes = [
        client.post(REQUEST_URL, json={"email": email}).status_code
        for email in [
            "known@example.com",
            "KNOWN@example.com",
            " known@example.com ",
            "known@example.com",
        ]
    ]

    assert codes == [204, 204, 204, 429]


def test_confirm_returns_no_content_without_signing_in(client, monkeypatch) -> None:
    received: dict[str, object] = {}

    async def fake_reset_password(**kwargs: object) -> None:
        received.update(kwargs)

    monkeypatch.setattr(auth_module, "reset_password", fake_reset_password)

    response = client.post(
        CONFIRM_URL, json={"token": "raw-token", "password": "a-brand-new-password"}
    )

    assert response.status_code == 204
    assert "set-cookie" not in response.headers
    assert received["token"] == "raw-token"
    assert received["new_password"] == "a-brand-new-password"


def test_confirm_returns_the_service_error_and_is_limited(client, monkeypatch) -> None:
    async def fake_reset_password(**_: object) -> None:
        raise AuthError(400, "password_reset_token_invalid", "Password reset link is invalid.")

    monkeypatch.setattr(auth_module, "reset_password", fake_reset_password)
    body = {"token": "bad-token", "password": "a-brand-new-password"}

    responses = [client.post(CONFIRM_URL, json=body) for _ in range(11)]

    assert responses[0].status_code == 400
    assert responses[0].json()["error"]["code"] == "password_reset_token_invalid"
    assert [response.status_code for response in responses] == [400] * 10 + [429]


def test_reset_endpoints_reject_a_foreign_origin(client, sent) -> None:
    response = client.post(
        REQUEST_URL,
        json={"email": "known@example.com"},
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert sent == []
