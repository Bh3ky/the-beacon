from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict

from rifthub_backend.auth.security import canonicalize_email
from rifthub_backend.auth.service import (
    SessionAuthResult,
    login_user,
    logout_session,
    register_user,
    resend_verification as resend_verification_email,
    verify_account,
)
from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserRole, UserStatus
from rifthub_backend.models.user import User

from rifthub_api.dependencies import (
    AppSettings,
    CurrentSessionDep,
    DbSession,
    RequiredCurrentSession,
    validate_session_csrf,
)
from rifthub_api.rate_limit import rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


class UserPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    bio: str | None
    role: UserRole
    status: UserStatus
    karma: int
    post_count: int
    comment_count: int
    avatar_url: str | None
    created_at: datetime
    last_active_at: datetime | None


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class VerifyRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ResendVerificationRequest(BaseModel):
    email: str


class RegisterResponse(BaseModel):
    verification_required: bool
    user: UserPayload


class AuthenticatedResponse(BaseModel):
    user: UserPayload


def _cookie_secure(settings: Settings) -> bool:
    return settings.environment not in {"development", "test"}


def _session_max_age(settings: Settings) -> int:
    return settings.session_absolute_hours * 60 * 60


def _set_auth_cookies(
    *,
    response: Response,
    settings: Settings,
    auth_result: SessionAuthResult,
) -> None:
    secure = _cookie_secure(settings)
    max_age = _session_max_age(settings)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=auth_result.raw_session_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=auth_result.csrf_token,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def _clear_auth_cookies(*, response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        secure=_cookie_secure(settings),
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        httponly=False,
        secure=_cookie_secure(settings),
        samesite="lax",
        path="/",
    )


def _client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _serialize_user(user: User) -> UserPayload:
    return UserPayload.model_validate(user)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: DbSession,
    settings: AppSettings,
) -> RegisterResponse:
    client_ip = _client_ip(request)
    await rate_limiter.check(
        key=f"register:hour:{client_ip}",
        limit=3,
        window_seconds=60 * 60,
        message="Too many registration attempts. Try again later.",
    )
    await rate_limiter.check(
        key=f"register:day:{client_ip}",
        limit=5,
        window_seconds=60 * 60 * 24,
        message="Too many registration attempts. Try again tomorrow.",
    )
    result = await register_user(
        db=db,
        settings=settings,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    return RegisterResponse(verification_required=True, user=_serialize_user(result.user))


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> Response:
    client_ip = _client_ip(request)
    await rate_limiter.check(
        key=f"resend:ip:{client_ip}",
        limit=3,
        window_seconds=60 * 60,
        message="Too many verification resend attempts. Try again later.",
    )
    email_key = payload.email.strip().lower()
    try:
        email_key = canonicalize_email(payload.email)
    except ValueError:
        pass
    await rate_limiter.check(
        key=f"resend:email:{email_key}",
        limit=5,
        window_seconds=60 * 60 * 24,
        message="Too many verification resend attempts for this account. Try again later.",
    )
    await resend_verification_email(
        db=db,
        settings=settings,
        email=payload.email,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/verify", response_model=AuthenticatedResponse)
async def verify(
    payload: VerifyRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> AuthenticatedResponse:
    client_ip = _client_ip(request)
    await rate_limiter.check(
        key=f"verify:{client_ip}",
        limit=10,
        window_seconds=60 * 60,
        message="Too many verification attempts. Try again later.",
    )
    result = await verify_account(
        db=db,
        settings=settings,
        token=payload.token,
    )
    _set_auth_cookies(response=response, settings=settings, auth_result=result)
    return AuthenticatedResponse(user=_serialize_user(result.user))


@router.post("/login", response_model=AuthenticatedResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> AuthenticatedResponse:
    client_ip = _client_ip(request)
    await rate_limiter.check(
        key=f"login:ip:{client_ip}",
        limit=5,
        window_seconds=60,
        message="Too many login attempts. Try again later.",
    )
    email_key = payload.email.strip().lower()
    try:
        email_key = canonicalize_email(payload.email)
    except ValueError:
        pass
    await rate_limiter.check(
        key=f"login:email:{email_key}",
        limit=10,
        window_seconds=15 * 60,
        message="Too many login attempts for this account. Try again later.",
    )
    result = await login_user(
        db=db,
        settings=settings,
        email=payload.email,
        password=payload.password,
    )
    _set_auth_cookies(response=response, settings=settings, auth_result=result)
    return AuthenticatedResponse(user=_serialize_user(result.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
    current_session: CurrentSessionDep,
) -> Response:
    if current_session is not None:
        validate_session_csrf(
            request=request,
            settings=settings,
            current_session=current_session,
        )
        await logout_session(db=db, session=current_session.session)
    _clear_auth_cookies(response=response, settings=settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AuthenticatedResponse)
async def me(
    response: Response,
    request: Request,
    settings: AppSettings,
    current_session: RequiredCurrentSession,
) -> AuthenticatedResponse:
    if not request.cookies.get(settings.csrf_cookie_name):
        response.set_cookie(
            key=settings.csrf_cookie_name,
            value=current_session.csrf_token,
            httponly=False,
            secure=_cookie_secure(settings),
            samesite="lax",
            max_age=_session_max_age(settings),
            path="/",
        )
    return AuthenticatedResponse(user=_serialize_user(current_session.user))
