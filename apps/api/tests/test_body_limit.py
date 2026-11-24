from collections.abc import Iterator

import rifthub_api.main as main_module
from fastapi.testclient import TestClient
from rifthub_api.body_limit import MAX_REQUEST_BODY_BYTES
from rifthub_backend.config import Settings


def build_client(monkeypatch) -> TestClient:
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )

    async def fake_ping_database(engine: object | None = None) -> None:
        return None

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: object())
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_ping_database)
    return TestClient(main_module.create_app())


def test_body_over_the_limit_is_rejected_with_413(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/login", content=b"x" * (MAX_REQUEST_BODY_BYTES + 1))

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_chunked_body_over_the_limit_is_rejected_with_413(monkeypatch) -> None:
    def chunks() -> Iterator[bytes]:
        for _ in range(MAX_REQUEST_BODY_BYTES // 1024 + 2):
            yield b"x" * 1024

    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/login", content=chunks())

    assert response.status_code == 413


def test_normal_sized_body_is_not_rejected(monkeypatch) -> None:
    with build_client(monkeypatch) as client:
        response = client.post("/v1/auth/login", json={"email": "a", "password": "b"})

    assert response.status_code != 413
