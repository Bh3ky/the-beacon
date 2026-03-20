from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import uvicorn

from rifthub_backend import (
    configure_logging,
    dispose_engine,
    get_engine,
    get_settings,
    ping_database,
)

from rifthub_api.errors import (
    ApiError,
    api_error_handler,
    auth_error_handler,
    creation_error_handler,
    error_response,
    flagging_error_handler,
    read_error_handler,
    validation_error_handler,
    voting_error_handler,
)
from rifthub_api.routes import auth_router, comments_router, feeds_router, flags_router, posts_router, stats_router
from rifthub_backend.auth.service import AuthError
from rifthub_backend.creation import CreationError
from rifthub_backend.flags import FlaggingError
from rifthub_backend.reads import ReadError
from rifthub_backend.voting import VotingError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            engine = get_engine()
            await ping_database(engine)
            logger.info("Starting RiftHub API in %s", settings.environment)
            yield
        finally:
            await dispose_engine()
            logger.info("Stopped RiftHub API")

    app = FastAPI(title="RiftHub API", lifespan=lifespan)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(AuthError, auth_error_handler)
    app.add_exception_handler(CreationError, creation_error_handler)
    app.add_exception_handler(FlaggingError, flagging_error_handler)
    app.add_exception_handler(ReadError, read_error_handler)
    app.add_exception_handler(VotingError, voting_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    @app.middleware("http")
    async def validate_origin(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            # Missing Origin is intentionally allowed for same-origin browser requests
            # and non-browser callers. Authenticated mutating routes still require the
            # session-bound CSRF check, so origin validation is not the only control.
            if origin is not None and origin not in settings.allowed_origins:
                return error_response(
                    status_code=403,
                    code="forbidden",
                    message="Origin is not allowed.",
                )
        return await call_next(request)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "service": "api",
            "status": "ok",
            "environment": settings.environment,
        }

    app.include_router(auth_router, prefix="/v1")
    app.include_router(comments_router, prefix="/v1")
    app.include_router(feeds_router, prefix="/v1")
    app.include_router(flags_router, prefix="/v1")
    app.include_router(posts_router, prefix="/v1")
    app.include_router(stats_router, prefix="/v1")

    return app


app = create_app()


def _run_server(*, reload: bool) -> None:
    settings = get_settings()
    uvicorn.run(
        "rifthub_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=reload,
    )


def run() -> None:
    _run_server(reload=False)


def run_dev() -> None:
    _run_server(reload=True)
