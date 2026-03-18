from uuid import uuid4

from rifthub_backend.auth.security import (
    canonicalize_email,
    canonicalize_username,
    generate_csrf_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_csrf_token,
    verify_password,
)


def test_canonicalize_email_lowercases_without_alias_stripping() -> None:
    assert canonicalize_email(" Foo.Bar+news@Gmail.COM ") == "foo.bar+news@gmail.com"


def test_canonicalize_username_lowercases_and_trims() -> None:
    assert canonicalize_username("  Bheki_1  ") == "bheki_1"


def test_password_hash_round_trip() -> None:
    stored_hash = hash_password("avery-strong-password")

    assert verify_password("avery-strong-password", stored_hash) is True
    assert verify_password("wrong-password", stored_hash) is False


def test_opaque_token_hash_is_deterministic() -> None:
    raw_token = generate_opaque_token()

    assert hash_opaque_token(raw_token) == hash_opaque_token(raw_token)


def test_csrf_token_is_session_bound() -> None:
    session_id = uuid4()
    session_token_hash = hash_opaque_token("raw-session-token")
    token = generate_csrf_token(
        session_id=session_id,
        session_token_hash=session_token_hash,
        secret="test-secret",
    )

    assert verify_csrf_token(expected_token=token, provided_token=token) is True
    assert (
        generate_csrf_token(
            session_id=uuid4(),
            session_token_hash=session_token_hash,
            secret="test-secret",
        )
        != token
    )
