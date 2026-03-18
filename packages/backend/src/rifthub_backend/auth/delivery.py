from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
import json
import logging
import smtplib
from typing import Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlencode

from rifthub_backend.config import ConfigError, Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VerificationDeliveryRequest:
    recipient_email: str
    username: str
    verification_url: str
    expires_at: datetime


class VerificationDeliveryPort(Protocol):
    async def send_verification(self, request: VerificationDeliveryRequest) -> None:
        """Send a verification message to the target user."""


def build_verification_url(*, settings: Settings, token: str) -> str:
    base_url = settings.frontend_base_url.rstrip("/")
    return f"{base_url}/verify?{urlencode({'token': token})}"


class NoopVerificationDelivery:
    async def send_verification(self, request: VerificationDeliveryRequest) -> None:
        logger.debug("Skipping verification delivery for %s", request.recipient_email)


class LoggingVerificationDelivery:
    async def send_verification(self, request: VerificationDeliveryRequest) -> None:
        logger.info(
            "Verification link for %s (%s): %s",
            request.username,
            request.recipient_email,
            request.verification_url,
        )


class MailpitVerificationDelivery:
    def __init__(
        self,
        *,
        from_email: str,
        host: str,
        port: int,
        starttls: bool,
    ) -> None:
        self._from_email = from_email
        self._host = host
        self._port = port
        self._starttls = starttls

    async def send_verification(self, request: VerificationDeliveryRequest) -> None:
        await asyncio.to_thread(self._send_sync, request)

    def _send_sync(self, request: VerificationDeliveryRequest) -> None:
        message = EmailMessage()
        message["Subject"] = "Verify your RiftHub account"
        message["From"] = self._from_email
        message["To"] = request.recipient_email
        message.set_content(
            "\n".join(
                [
                    f"Hi {request.username},",
                    "",
                    "Complete your RiftHub account verification by opening this link:",
                    request.verification_url,
                    "",
                    f"This link expires at {request.expires_at.isoformat()}.",
                ]
            )
        )

        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            if self._starttls:
                smtp.starttls()
            smtp.send_message(message)


class ResendVerificationDelivery:
    _endpoint = "https://api.resend.com/emails"

    def __init__(
        self,
        *,
        api_key: str,
        from_email: str,
    ) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send_verification(self, request: VerificationDeliveryRequest) -> None:
        await asyncio.to_thread(self._send_sync, request)

    def _send_sync(self, request: VerificationDeliveryRequest) -> None:
        payload = {
            "from": self._from_email,
            "to": [request.recipient_email],
            "subject": "Verify your RiftHub account",
            "text": "\n".join(
                [
                    f"Hi {request.username},",
                    "",
                    "Complete your RiftHub account verification by opening this link:",
                    request.verification_url,
                    "",
                    f"This link expires at {request.expires_at.isoformat()}.",
                ]
            ),
        }
        body = json.dumps(payload).encode("utf-8")
        request_obj = urllib_request.Request(
            self._endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "rifthub-backend/0.1",
            },
        )
        try:
            with urllib_request.urlopen(request_obj, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(f"Resend returned unexpected status {response.status}.")
        except urllib_error.HTTPError as exc:  # pragma: no cover - network/provider error handling
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Resend email delivery failed with status {exc.code}: {detail}"
            ) from exc
        except urllib_error.URLError as exc:  # pragma: no cover - network/provider error handling
            raise RuntimeError(f"Resend email delivery failed: {exc.reason}") from exc


def get_verification_delivery(settings: Settings) -> VerificationDeliveryPort:
    mode = settings.verification_delivery_mode
    if mode == "noop":
        return NoopVerificationDelivery()
    if mode == "log":
        if settings.environment not in {"development", "test"}:
            raise ConfigError(
                "RIFTHUB_VERIFICATION_DELIVERY_MODE=log is only allowed in development or test."
            )
        return LoggingVerificationDelivery()
    if mode == "mailpit":
        return MailpitVerificationDelivery(
            from_email=settings.verification_from_email,
            host=settings.verification_smtp_host,
            port=settings.verification_smtp_port,
            starttls=settings.verification_smtp_starttls,
        )
    if mode == "resend":
        if not settings.resend_api_key:
            raise ConfigError(
                "RIFTHUB_RESEND_API_KEY is required when RIFTHUB_VERIFICATION_DELIVERY_MODE=resend."
            )
        return ResendVerificationDelivery(
            api_key=settings.resend_api_key,
            from_email=settings.verification_from_email,
        )
    raise ConfigError(f"Unsupported verification delivery mode: {mode}")
