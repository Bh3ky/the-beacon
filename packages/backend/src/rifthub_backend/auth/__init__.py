"""Auth service helpers for RiftHub."""

from .delivery import build_verification_url, get_verification_delivery
from .security import (
    canonicalize_email,
    canonicalize_username,
    generate_csrf_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    is_valid_email,
    validate_password,
    verify_password,
)

__all__ = [
    "canonicalize_email",
    "canonicalize_username",
    "build_verification_url",
    "generate_csrf_token",
    "generate_opaque_token",
    "get_verification_delivery",
    "hash_opaque_token",
    "hash_password",
    "is_valid_email",
    "validate_password",
    "verify_password",
]
