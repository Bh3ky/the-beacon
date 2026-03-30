from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rifthub_backend.auth.security import canonicalize_email
from rifthub_backend.db.types import UserRole
from rifthub_backend.models.user import User


@dataclass(slots=True)
class RoleAssignmentError(Exception):
    status_code: int
    code: str
    message: str


async def assign_user_role(
    *,
    db: AsyncSession,
    email: str,
    role: UserRole,
) -> User:
    try:
        canonical_email = canonicalize_email(email)
    except ValueError as exc:
        raise RoleAssignmentError(422, "validation_error", str(exc)) from exc

    user = await db.scalar(select(User).where(User.email == canonical_email))
    if user is None:
        raise RoleAssignmentError(404, "user_not_found", "The requested user does not exist.")

    user.role = role
    await db.commit()
    await db.refresh(user)
    return user
