from __future__ import annotations

from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac, sha256
import hmac
import os
import re
import secrets
from uuid import UUID


_PASSWORD_ITERATIONS = 600_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[a-z0-9_]{3,32}$")


def canonicalize_email(raw: str) -> str:
    email = raw.strip().lower()
    local, separator, domain = email.partition("@")
    if not separator or not local or not domain:
        raise ValueError("Invalid email address.")
    return f"{local}@{domain}"


def is_valid_email(raw: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(raw.strip()))


def canonicalize_username(raw: str) -> str:
    username = raw.strip().lower()
    if not _USERNAME_RE.fullmatch(username):
        raise ValueError(
            "Username must be 3-32 characters and contain only lowercase letters, digits, and underscores."
        )
    return username


def validate_password(raw: str) -> str:
    if len(raw) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    if len(raw) > 256:
        raise ValueError("Password must be at most 256 characters long.")
    return raw


def hash_password(raw_password: str) -> str:
    password = validate_password(raw_password)
    salt = os.urandom(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        algorithm, raw_iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived = pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(raw_iterations),
    )
    return hmac.compare_digest(derived.hex(), digest_hex)


def generate_opaque_token() -> str:
    return urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def hash_opaque_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def generate_csrf_token(*, session_id: UUID, session_token_hash: str, secret: str) -> str:
    payload = f"{session_id}:{session_token_hash}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, sha256).hexdigest()


def verify_csrf_token(*, expected_token: str, provided_token: str) -> bool:
    return hmac.compare_digest(expected_token, provided_token)
