from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Protocol

from rifthub_backend.auth.service import AuthError
from rifthub_backend.creation import CreationError
from rifthub_backend.flags import FlaggingError
from rifthub_backend.moderation import ModerationError
from rifthub_backend.reads import ReadError
from rifthub_backend.voting import VotingError


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class _StructuredApiError(Protocol):
    status_code: int
    code: str
    message: str
    details: object | None


def _custom_error_response(exc: _StructuredApiError) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )


async def api_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return _custom_error_response(exc)


async def auth_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AuthError)
    return _custom_error_response(exc)


async def read_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ReadError)
    return _custom_error_response(exc)


async def creation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CreationError)
    return _custom_error_response(exc)


async def flagging_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, FlaggingError)
    return _custom_error_response(exc)


async def moderation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ModerationError)
    return _custom_error_response(exc)


async def voting_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, VotingError)
    return _custom_error_response(exc)


async def validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=exc.errors(),
    )
