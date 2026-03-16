import asyncio

import pytest

from rifthub_backend.config import Settings
import rifthub_backend.db.session as session_module


class DummyEngine:
    def __init__(self) -> None:
        self.dispose_calls = 0

    async def dispose(self) -> None:
        self.dispose_calls += 1


def make_settings(
    *,
    database_url: str,
    sql_echo: bool = False,
    environment: str = "test",
    api_port: int = 8000,
) -> Settings:
    return Settings(
        environment=environment,
        log_level="INFO",
        api_host="127.0.0.1",
        api_port=api_port,
        database_url=database_url,
        migration_database_url=database_url,
        sql_echo=sql_echo,
    )


@pytest.fixture(autouse=True)
def reset_session_state() -> None:
    asyncio.run(session_module.dispose_engine())
    yield
    asyncio.run(session_module.dispose_engine())


def test_get_engine_reuses_cached_engine_for_same_effective_config(monkeypatch) -> None:
    created: list[tuple[DummyEngine, str, bool, bool]] = []

    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        engine = DummyEngine()
        created.append((engine, database_url, echo, pool_pre_ping))
        return engine

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)

    engine = session_module.get_engine(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
            sql_echo=True,
            environment="test",
        )
    )
    reused_engine = session_module.get_engine(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
            sql_echo=True,
            environment="production",
            api_port=9000,
        )
    )

    assert reused_engine is engine
    assert created == [
        (
            engine,
            "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
            True,
            True,
        )
    ]


def test_get_engine_rejects_reconfiguration_without_dispose(monkeypatch) -> None:
    created: list[DummyEngine] = []

    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        del database_url, echo, pool_pre_ping
        engine = DummyEngine()
        created.append(engine)
        return engine

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)

    session_module.get_engine(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
        )
    )

    with pytest.raises(RuntimeError, match="dispose_engine\\(\\)"):
        session_module.get_engine(
            make_settings(
                database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_other",
            )
        )

    assert len(created) == 1


def test_get_session_factory_reuses_cached_factory_for_same_effective_config(
    monkeypatch,
) -> None:
    created_engines: list[DummyEngine] = []
    created_factories: list[tuple[object, DummyEngine, bool]] = []

    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        del database_url, echo, pool_pre_ping
        engine = DummyEngine()
        created_engines.append(engine)
        return engine

    def fake_async_sessionmaker(*, bind: DummyEngine, expire_on_commit: bool) -> object:
        factory = object()
        created_factories.append((factory, bind, expire_on_commit))
        return factory

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_async_sessionmaker)

    factory = session_module.get_session_factory(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
            sql_echo=True,
        )
    )
    reused_factory = session_module.get_session_factory(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
            sql_echo=True,
            environment="development",
            api_port=9001,
        )
    )

    assert reused_factory is factory
    assert len(created_engines) == 1
    assert created_factories == [(factory, created_engines[0], False)]


def test_get_session_factory_rejects_reconfiguration_without_dispose(
    monkeypatch,
) -> None:
    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        del database_url, echo, pool_pre_ping
        return DummyEngine()

    def fake_async_sessionmaker(*, bind: DummyEngine, expire_on_commit: bool) -> object:
        del bind, expire_on_commit
        return object()

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_async_sessionmaker)

    session_module.get_session_factory(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
        )
    )

    with pytest.raises(RuntimeError, match="dispose_engine\\(\\)"):
        session_module.get_session_factory(
            make_settings(
                database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_other",
            )
        )


def test_dispose_engine_resets_cache_for_new_configuration(monkeypatch) -> None:
    created_engines: list[DummyEngine] = []
    created_factories: list[object] = []

    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        del database_url, echo, pool_pre_ping
        engine = DummyEngine()
        created_engines.append(engine)
        return engine

    def fake_async_sessionmaker(*, bind: DummyEngine, expire_on_commit: bool) -> object:
        del bind, expire_on_commit
        factory = object()
        created_factories.append(factory)
        return factory

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(session_module, "async_sessionmaker", fake_async_sessionmaker)

    first_factory = session_module.get_session_factory(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
        )
    )
    first_engine = created_engines[0]

    asyncio.run(session_module.dispose_engine())

    second_factory = session_module.get_session_factory(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_other",
        )
    )

    assert first_engine.dispose_calls == 1
    assert second_factory is not first_factory
    assert len(created_engines) == 2
    assert len(created_factories) == 2


def test_dispose_engine_clears_cache_even_if_dispose_fails(monkeypatch) -> None:
    class FailingEngine(DummyEngine):
        async def dispose(self) -> None:
            self.dispose_calls += 1
            raise RuntimeError("dispose failed")

    created_engines: list[DummyEngine] = []

    def fake_create_async_engine(
        database_url: str,
        *,
        echo: bool,
        pool_pre_ping: bool,
    ) -> DummyEngine:
        del database_url, echo, pool_pre_ping
        engine: DummyEngine
        if not created_engines:
            engine = FailingEngine()
        else:
            engine = DummyEngine()
        created_engines.append(engine)
        return engine

    monkeypatch.setattr(session_module, "create_async_engine", fake_create_async_engine)

    session_module.get_engine(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub",
        )
    )

    with pytest.raises(RuntimeError, match="dispose failed"):
        asyncio.run(session_module.dispose_engine())

    replacement_engine = session_module.get_engine(
        make_settings(
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_other",
        )
    )

    assert replacement_engine is created_engines[1]


def test_ping_database_executes_select_one() -> None:
    executed_statements: list[str] = []

    class DummyConnection:
        async def __aenter__(self) -> "DummyConnection":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        async def execute(self, statement) -> None:
            executed_statements.append(str(statement))

    class PingEngine:
        def connect(self) -> DummyConnection:
            return DummyConnection()

    asyncio.run(session_module.ping_database(PingEngine()))

    assert executed_statements == ["SELECT 1"]
