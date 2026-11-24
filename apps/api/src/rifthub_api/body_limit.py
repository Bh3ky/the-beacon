from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from rifthub_api.errors import error_response

MAX_REQUEST_BODY_BYTES = 256 * 1024


class MaxBodySizeMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared_length = dict(scope["headers"]).get(b"content-length", b"")
        if declared_length.isdigit() and int(declared_length) > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        received_bytes = 0
        response_started = False
        rejected = False

        async def counting_receive() -> Message:
            nonlocal received_bytes, rejected
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes and not response_started:
                    rejected = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if rejected:
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, counting_receive, guarded_send)
        except Exception:
            if not rejected:
                raise

        if rejected:
            await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(
            status_code=413,
            code="payload_too_large",
            message="Request body is too large.",
        )
        await response(scope, receive, send)
