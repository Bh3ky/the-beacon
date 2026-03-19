from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from rifthub_backend.config import Settings
from rifthub_backend.summary import PlatformSummarySnapshot

import rifthub_api.dependencies as dependencies_module
import rifthub_api.main as main_module
import rifthub_api.routes.stats as stats_module


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


def build_client(monkeypatch) -> TestClient:
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
    return TestClient(app)


def test_platform_summary_returns_expected_payload(monkeypatch) -> None:
    async def fake_get_platform_summary(_: object) -> PlatformSummarySnapshot:
        return PlatformSummarySnapshot(
            builders_this_month=847,
            builders_delta_pct=18.4,
            funding_stories_last_30d=132,
            funding_stories_delta_pct=9.1,
            posts_per_hour=6.0,
            posts_per_hour_delta_pct=22.4,
            comments_this_week=1942,
            comments_delta_pct=-3.5,
            jobs_live=18,
            jobs_live_delta_pct=12.5,
        )

    monkeypatch.setattr(stats_module, "get_platform_summary", fake_get_platform_summary)

    with build_client(monkeypatch) as client:
        response = client.get("/v1/stats/summary")

    assert response.status_code == 200
    assert response.json() == {
        "builders_this_month": 847,
        "builders_delta_pct": 18.4,
        "funding_stories_last_30d": 132,
        "funding_stories_delta_pct": 9.1,
        "posts_per_hour": 6.0,
        "posts_per_hour_delta_pct": 22.4,
        "comments_this_week": 1942,
        "comments_delta_pct": -3.5,
        "jobs_live": 18,
        "jobs_live_delta_pct": 12.5,
    }
