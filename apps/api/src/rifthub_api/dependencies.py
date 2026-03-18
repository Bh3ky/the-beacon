from __future__ import annotations

from collections.abc import AsyncIterator
import hmac
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend import get_async_session, get_settings
from rifthub_backend.auth.security import verify_csrf_token
from rifthub_backend.auth.service import CurrentSession, resolve_current_session
from rifthub_backend.config import Settings

from .errors import ApiError


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_session(
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> CurrentSession | None:
    # Optional-auth routes intentionally collapse "missing session" and
    # "invalid/expired session" into the same None result.
    raw_session_token = request.cookies.get(settings.session_cookie_name)
    return await resolve_current_session(
        db=db,
        settings=settings,
        raw_session_token=raw_session_token,
    )


CurrentSessionDep = Annotated[CurrentSession | None, Depends(get_current_session)]


def require_authenticated_session(current_session: CurrentSessionDep) -> CurrentSession:
    if current_session is None:
        raise ApiError(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
        )
    return current_session


RequiredCurrentSession = Annotated[CurrentSession, Depends(require_authenticated_session)]


def validate_session_csrf(
    *,
    request: Request,
    settings: Settings,
    current_session: CurrentSession,
) -> None:
    header_token = request.headers.get("X-CSRF-Token")
    cookie_token = request.cookies.get(settings.csrf_cookie_name)

    if not header_token or not cookie_token:
        raise ApiError(
            status_code=403,
            code="forbidden",
            message="CSRF validation failed.",
        )
    if not hmac.compare_digest(header_token, cookie_token):
        raise ApiError(
            status_code=403,
            code="forbidden",
            message="CSRF validation failed.",
        )
    if not verify_csrf_token(
        expected_token=current_session.csrf_token,
        provided_token=header_token,
    ):
        raise ApiError(
            status_code=403,
            code="forbidden",
            message="CSRF validation failed.",
        )
