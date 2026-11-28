from __future__ import annotations

import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from typing import Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlencode

from rifthub_backend.config import ConfigError, Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OutgoingEmail:
    recipient_email: str
    subject: str
    text: str


@dataclass(frozen=True, slots=True)
class EmailDeliveryResult:
    provider_message_id: str | None = None


class EmailDeliveryPort(Protocol):
    async def send(self, email: OutgoingEmail) -> EmailDeliveryResult:
        """Send one email."""


def build_verification_url(*, settings: Settings, token: str) -> str:
    base_url = settings.frontend_base_url.rstrip("/")
    return f"{base_url}/verify?{urlencode({'token': token})}"


def build_verification_email(
    *,
    recipient_email: str,
    username: str,
    verification_url: str,
    expires_at: datetime,
) -> OutgoingEmail:
    return OutgoingEmail(
        recipient_email=recipient_email,
        subject="Verify your RiftHub account",
        text="\n".join(
            [
                f"Hi {username},",
                "",
                "Complete your RiftHub account verification by opening this link:",
                verification_url,
                "",
                f"This link expires at {expires_at.isoformat()}.",
            ]
        ),
    )


class NoopEmailDelivery:
    async def send(self, email: OutgoingEmail) -> EmailDeliveryResult:
        logger.debug("Skipping email delivery to %s", email.recipient_email)
        return EmailDeliveryResult()


class LoggingEmailDelivery:
    async def send(self, email: OutgoingEmail) -> EmailDeliveryResult:
        logger.info(
            "Email to %s: %s\n%s",
            email.recipient_email,
            email.subject,
            email.text,
        )
        return EmailDeliveryResult()


class MailpitEmailDelivery:
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

    async def send(self, email: OutgoingEmail) -> EmailDeliveryResult:
        return await asyncio.to_thread(self._send_sync, email)

    def _send_sync(self, email: OutgoingEmail) -> EmailDeliveryResult:
        message = EmailMessage()
        message["Subject"] = email.subject
        message["From"] = self._from_email
        message["To"] = email.recipient_email
        message.set_content(email.text)

        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            if self._starttls:
                smtp.starttls()
            smtp.send_message(message)
        return EmailDeliveryResult()


class ResendEmailDelivery:
    _endpoint = "https://api.resend.com/emails"

    def __init__(
        self,
        *,
        api_key: str,
        from_email: str,
    ) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send(self, email: OutgoingEmail) -> EmailDeliveryResult:
        return await asyncio.to_thread(self._send_sync, email)

    def _send_sync(self, email: OutgoingEmail) -> EmailDeliveryResult:
        payload = {
            "from": self._from_email,
            "to": [email.recipient_email],
            "subject": email.subject,
            "text": email.text,
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
                raw_body = response.read().decode("utf-8", errors="replace")
        except urllib_error.HTTPError as exc:  # pragma: no cover - network/provider error handling
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Resend email delivery failed with status {exc.code}: {detail}"
            ) from exc
        except urllib_error.URLError as exc:  # pragma: no cover - network/provider error handling
            raise RuntimeError(f"Resend email delivery failed: {exc.reason}") from exc

        provider_message_id = None
        if raw_body:
            try:
                parsed = json.loads(raw_body)
            except json.JSONDecodeError:
                logger.warning("Resend returned non-JSON body for email delivery.")
            else:
                if isinstance(parsed, dict):
                    if isinstance(parsed.get("id"), str):
                        provider_message_id = parsed["id"]
                    elif isinstance(parsed.get("data"), dict) and isinstance(parsed["data"].get("id"), str):
                        provider_message_id = parsed["data"]["id"]

        return EmailDeliveryResult(provider_message_id=provider_message_id)


def get_email_delivery(settings: Settings) -> EmailDeliveryPort:
    mode = settings.verification_delivery_mode
    if mode == "noop":
        return NoopEmailDelivery()
    if mode == "log":
        if settings.environment not in {"development", "test"}:
            raise ConfigError(
                "RIFTHUB_VERIFICATION_DELIVERY_MODE=log is only allowed in development or test."
            )
        return LoggingEmailDelivery()
    if mode == "mailpit":
        return MailpitEmailDelivery(
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
        return ResendEmailDelivery(
            api_key=settings.resend_api_key,
            from_email=settings.verification_from_email,
        )
    raise ConfigError(f"Unsupported verification delivery mode: {mode}")
