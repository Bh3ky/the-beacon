from __future__ import annotations

import argparse
import asyncio

from rifthub_backend import get_async_session
from rifthub_backend.db.types import UserRole
from rifthub_backend.user_roles import RoleAssignmentError, assign_user_role


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assign a RiftHub user role by email.")
    parser.add_argument("--email", required=True, help="Email address of the existing user account.")
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in UserRole],
        help="Role to assign.",
    )
    return parser


async def main() -> int:
    args = build_parser().parse_args()
    async for db in get_async_session():
        try:
            user = await assign_user_role(
                db=db,
                email=args.email,
                role=UserRole(args.role),
            )
        except RoleAssignmentError as exc:
            print(f"[error] {exc.code}: {exc.message}")
            return 1

        print(f"[ok] {user.email} -> role={user.role.value}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
