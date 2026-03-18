from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from rifthub_backend.config import Settings
from rifthub_backend.db.types import UserStatus
from rifthub_backend.models.session import UserSession
from rifthub_backend.models.user import User
from rifthub_backend.models.verification import UserVerificationToken

from .delivery import (
    VerificationDeliveryRequest,
    build_verification_url,
    get_verification_delivery,
)
from .security import (
    canonicalize_email,
    canonicalize_username,
    generate_csrf_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    is_valid_email,
    verify_password,
)

logger = logging.getLogger(__name__)

_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-parity")
ACTIVE_VERIFICATION_TOKEN_CONSTRAINT_NAME = "uq_user_verification_tokens_active_user_id"


@dataclass(slots=True)
class AuthError(Exception):
    status_code: int
    code: str
    message: str
    details: object | None = None


@dataclass(slots=True)
class PendingRegistration:
    user: User
    verification_token: str | None = None


@dataclass(slots=True)
class SessionAuthResult:
    user: User
    session: UserSession
    raw_session_token: str
    csrf_token: str


@dataclass(slots=True)
class CurrentSession:
    user: User
    session: UserSession
    csrf_token: str


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _absolute_session_expiry(*, now: datetime, settings: Settings) -> datetime:
    return now + timedelta(hours=settings.session_absolute_hours)


def _effective_session_expiry(*, now: datetime, created_at: datetime, settings: Settings) -> datetime:
    idle_expiry = now + timedelta(minutes=settings.session_idle_minutes)
    absolute_expiry = created_at + timedelta(hours=settings.session_absolute_hours)
    return min(idle_expiry, absolute_expiry)


def _session_is_expired(*, now: datetime, session: UserSession, settings: Settings) -> bool:
    if now >= session.expires_at:
        return True
    return now >= _absolute_session_expiry(now=session.created_at, settings=settings)


def _csrf_for_session(*, session: UserSession, settings: Settings) -> str:
    return generate_csrf_token(
        session_id=session.id,
        session_token_hash=session.session_token_hash,
        secret=settings.app_secret,
    )


def _verification_expiry(*, now: datetime, settings: Settings) -> datetime:
    return now + timedelta(hours=settings.verification_token_ttl_hours)


def _is_active_verification_token_conflict(exc: IntegrityError) -> bool:
    constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    return constraint_name == ACTIVE_VERIFICATION_TOKEN_CONSTRAINT_NAME


async def _create_verification_token(
    *,
    db: AsyncSession,
    user: User,
    settings: Settings,
    now: datetime,
) -> tuple[str, datetime]:
    await db.execute(delete(UserVerificationToken).where(UserVerificationToken.user_id == user.id))

    raw_token = generate_opaque_token()
    expires_at = _verification_expiry(now=now, settings=settings)
    db.add(
        UserVerificationToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_token),
            expires_at=expires_at,
            created_at=now,
        )
    )
    await db.flush()
    return raw_token, expires_at


async def _dispatch_verification(
    *,
    settings: Settings,
    user: User,
    raw_token: str,
    expires_at: datetime,
) -> None:
    delivery = get_verification_delivery(settings)
    request = VerificationDeliveryRequest(
        recipient_email=user.email,
        username=user.username,
        verification_url=build_verification_url(settings=settings, token=raw_token),
        expires_at=expires_at,
    )
    try:
        await delivery.send_verification(request)
    except Exception:  # pragma: no cover - defensive logging around external delivery
        logger.exception("Verification delivery failed for %s", user.email)


async def _create_session(
    *,
    db: AsyncSession,
    settings: Settings,
    user: User,
    now: datetime,
) -> SessionAuthResult:
    raw_session_token = generate_opaque_token()
    session = UserSession(
        user_id=user.id,
        session_token_hash=hash_opaque_token(raw_session_token),
        expires_at=_effective_session_expiry(now=now, created_at=now, settings=settings),
        created_at=now,
        last_seen_at=now,
    )
    db.add(session)
    await db.flush()
    csrf_token = _csrf_for_session(session=session, settings=settings)
    return SessionAuthResult(
        user=user,
        session=session,
        raw_session_token=raw_session_token,
        csrf_token=csrf_token,
    )


async def register_user(
    *,
    db: AsyncSession,
    settings: Settings,
    username: str,
    email: str,
    password: str,
) -> PendingRegistration:
    now = _utcnow()

    try:
        canonical_username = canonicalize_username(username)
    except ValueError as exc:
        raise AuthError(422, "validation_error", str(exc)) from exc

    if not is_valid_email(email):
        raise AuthError(422, "validation_error", "Email address is invalid.")

    try:
        canonical_email = canonicalize_email(email)
    except ValueError as exc:
        raise AuthError(422, "validation_error", str(exc)) from exc

    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        raise AuthError(422, "validation_error", str(exc)) from exc

    existing_user = await db.scalar(select(User).where(User.username == canonical_username))
    if existing_user is not None:
        raise AuthError(409, "duplicate_username", "Username is already in use.")

    existing_email = await db.scalar(select(User).where(User.email == canonical_email))
    if existing_email is not None:
        raise AuthError(409, "duplicate_email", "Email is already in use.")

    user = User(
        username=canonical_username,
        email=canonical_email,
        password_hash=password_hash,
        status=UserStatus.PENDING,
    )
    db.add(user)
    await db.flush()

    raw_verification_token, expires_at = await _create_verification_token(
        db=db,
        user=user,
        settings=settings,
        now=now,
    )
    await db.commit()
    await db.refresh(user)
    await _dispatch_verification(
        settings=settings,
        user=user,
        raw_token=raw_verification_token,
        expires_at=expires_at,
    )

    logger.info("Created pending account for %s", user.username)

    return PendingRegistration(user=user)


async def verify_account(
    *,
    db: AsyncSession,
    settings: Settings,
    token: str,
) -> SessionAuthResult:
    token_hash = hash_opaque_token(token)
    token_row = await db.scalar(
        select(UserVerificationToken)
        .options(joinedload(UserVerificationToken.user))
        .where(UserVerificationToken.token_hash == token_hash)
    )
    if token_row is None:
        raise AuthError(400, "verification_token_invalid", "Verification token is invalid.")

    now = _utcnow()
    if token_row.consumed_at is not None or token_row.user.status is UserStatus.ACTIVE:
        raise AuthError(409, "conflict", "Account is already verified.")
    if now >= token_row.expires_at:
        raise AuthError(400, "verification_token_expired", "Verification token has expired.")

    user = token_row.user
    user.status = UserStatus.ACTIVE
    user.last_active_at = now
    token_row.consumed_at = now

    await db.execute(
        delete(UserVerificationToken).where(
            UserVerificationToken.user_id == user.id,
            UserVerificationToken.id != token_row.id,
        )
    )
    result = await _create_session(db=db, settings=settings, user=user, now=now)
    await db.commit()
    await db.refresh(user)
    return result


async def resend_verification(
    *,
    db: AsyncSession,
    settings: Settings,
    email: str,
) -> None:
    if not is_valid_email(email):
        raise AuthError(422, "validation_error", "Email address is invalid.")

    try:
        canonical_email = canonicalize_email(email)
    except ValueError as exc:
        raise AuthError(422, "validation_error", str(exc)) from exc

    user = await db.scalar(select(User).where(User.email == canonical_email).with_for_update())
    if user is None or user.status is not UserStatus.PENDING:
        return

    now = _utcnow()
    try:
        raw_verification_token, expires_at = await _create_verification_token(
            db=db,
            user=user,
            settings=settings,
            now=now,
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if _is_active_verification_token_conflict(exc):
            return
        raise
    await _dispatch_verification(
        settings=settings,
        user=user,
        raw_token=raw_verification_token,
        expires_at=expires_at,
    )


async def login_user(
    *,
    db: AsyncSession,
    settings: Settings,
    email: str,
    password: str,
) -> SessionAuthResult:
    if not is_valid_email(email):
        raise AuthError(401, "invalid_credentials", "Invalid credentials.")

    try:
        canonical_email = canonicalize_email(email)
    except ValueError:
        raise AuthError(401, "invalid_credentials", "Invalid credentials.") from None

    user = await db.scalar(select(User).where(User.email == canonical_email))
    if user is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        raise AuthError(401, "invalid_credentials", "Invalid credentials.")
    if not verify_password(password, user.password_hash):
        raise AuthError(401, "invalid_credentials", "Invalid credentials.")
    if user.status is UserStatus.PENDING:
        raise AuthError(
            403,
            "account_pending_verification",
            "Account is pending verification.",
        )
    if user.status in {UserStatus.SUSPENDED, UserStatus.BANNED}:
        raise AuthError(403, "forbidden", "Account is suspended or banned.")

    now = _utcnow()
    user.last_active_at = now
    result = await _create_session(db=db, settings=settings, user=user, now=now)
    await db.commit()
    await db.refresh(user)
    return result


async def resolve_current_session(
    *,
    db: AsyncSession,
    settings: Settings,
    raw_session_token: str | None,
) -> CurrentSession | None:
    if not raw_session_token:
        return None

    token_hash = hash_opaque_token(raw_session_token)
    session = await db.scalar(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.session_token_hash == token_hash)
    )
    if session is None:
        return None

    now = _utcnow()
    if _session_is_expired(now=now, session=session, settings=settings):
        await db.delete(session)
        await db.commit()
        return None

    user = session.user
    if user.status is not UserStatus.ACTIVE:
        return None

    touch_interval = timedelta(minutes=settings.session_touch_interval_minutes)
    if session.last_seen_at is None or (now - session.last_seen_at) >= touch_interval:
        session.last_seen_at = now
        session.expires_at = _effective_session_expiry(
            now=now,
            created_at=session.created_at,
            settings=settings,
        )
        await db.commit()

    return CurrentSession(
        user=user,
        session=session,
        csrf_token=_csrf_for_session(session=session, settings=settings),
    )


async def logout_session(*, db: AsyncSession, session: UserSession | None) -> None:
    if session is None:
        return

    await db.delete(session)
    await db.commit()
