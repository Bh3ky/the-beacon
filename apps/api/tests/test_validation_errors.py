from fastapi.testclient import TestClient

from rifthub_backend.config import Settings
import rifthub_api.main as main_module


def test_non_json_body_returns_422_not_500(monkeypatch) -> None:
    # Same setup as test_health.py: fake settings and fake DB startup/shutdown,
    # so this test never needs a real database.
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )

    async def fake_ping_database(engine: object | None = None) -> None:
        pass

    async def fake_dispose_engine() -> None:
        pass

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: object())
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_dispose_engine)

    with TestClient(main_module.create_app()) as client:
        # data=... sends form data, not JSON. This is the request that used to crash.
        response = client.post("/v1/auth/login", data={"x": "1"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
