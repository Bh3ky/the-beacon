from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
import uvicorn

from rifthub_backend import (
    configure_logging,
    dispose_engine,
    get_engine,
    get_settings,
    ping_database,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        configure_logging(settings.log_level)
        try:
            engine = get_engine()
            await ping_database(engine)
            logger.info("Starting RiftHub API in %s", settings.environment)
            yield
        finally:
            await dispose_engine()
            logger.info("Stopped RiftHub API")

    app = FastAPI(title="RiftHub API", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "service": "api",
            "status": "ok",
            "environment": settings.environment,
        }

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "rifthub_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
