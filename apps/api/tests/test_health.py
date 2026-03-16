from fastapi.testclient import TestClient

from rifthub_backend.config import Settings
import rifthub_api.main as main_module


def test_health(monkeypatch) -> None:
    settings = Settings(
        environment="test",
        log_level="INFO",
        api_host="127.0.0.1",
        api_port=8000,
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        migration_database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
        sql_echo=False,
    )
    fake_engine = object()
    ping_calls: list[object | None] = []
    dispose_calls = 0

    async def fake_ping_database(engine: object | None = None) -> None:
        ping_calls.append(engine)

    async def fake_dispose_engine() -> None:
        nonlocal dispose_calls
        dispose_calls += 1

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_engine", lambda: fake_engine)
    monkeypatch.setattr(main_module, "ping_database", fake_ping_database)
    monkeypatch.setattr(main_module, "dispose_engine", fake_dispose_engine)

    with TestClient(main_module.create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "api",
        "status": "ok",
        "environment": "test",
    }
    assert ping_calls == [fake_engine]
    assert dispose_calls == 1
