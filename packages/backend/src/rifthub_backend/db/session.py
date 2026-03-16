from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from rifthub_backend.config import Settings, get_settings


@dataclass(frozen=True)
class _EngineConfig:
    database_url: str
    sql_echo: bool


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_engine_config: _EngineConfig | None = None
_session_factory_config: _EngineConfig | None = None


def _resolve_engine_config(settings: Settings | None) -> _EngineConfig:
    resolved_settings = settings if settings is not None else get_settings()
    return _EngineConfig(
        database_url=resolved_settings.database_url,
        sql_echo=resolved_settings.sql_echo,
    )


def _ensure_matching_config(
    *,
    resource_name: str,
    cached_config: _EngineConfig | None,
    requested_config: _EngineConfig,
) -> None:
    if cached_config is None or cached_config == requested_config:
        return

    raise RuntimeError(
        f"{resource_name} is already initialized for "
        f"database_url={cached_config.database_url!r} and "
        f"sql_echo={cached_config.sql_echo!r}; "
        "call dispose_engine() before reinitializing with different database settings."
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine, _engine_config

    requested_config = _resolve_engine_config(settings)
    _ensure_matching_config(
        resource_name="Database engine",
        cached_config=_engine_config,
        requested_config=requested_config,
    )

    if _engine is None:
        _engine = create_async_engine(
            requested_config.database_url,
            echo=requested_config.sql_echo,
            pool_pre_ping=True,
        )
        _engine_config = requested_config

    return _engine


def get_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    global _session_factory, _session_factory_config

    requested_config = _resolve_engine_config(settings)
    _ensure_matching_config(
        resource_name="Session factory",
        cached_config=_session_factory_config,
        requested_config=requested_config,
    )

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(settings),
            expire_on_commit=False,
        )
        _session_factory_config = requested_config

    return _session_factory


async def get_async_session(settings: Settings | None = None) -> AsyncIterator[AsyncSession]:
    async with get_session_factory(settings)() as session:
        yield session


async def ping_database(engine: AsyncEngine | None = None) -> None:
    target_engine = engine or get_engine()

    async with target_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dispose_engine() -> None:
    global _engine, _session_factory, _engine_config, _session_factory_config

    engine = _engine
    _engine = None
    _session_factory = None
    _engine_config = None
    _session_factory_config = None

    if engine is not None:
        await engine.dispose()
