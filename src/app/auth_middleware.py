"""
ASGI Basic Auth Middleware for the CdE Dashboard.

Wraps any ASGI app with HTTP Basic Authentication.
Credentials are loaded from environment variables or a .env file.
"""

import base64
import hashlib
import hmac
import os
from pathlib import Path


def _load_env_file():
    """Load credentials from .env file if it exists."""
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


class BasicAuthMiddleware:
    """
    ASGI middleware that enforces HTTP Basic Authentication.

    Usage:
        from auth_middleware import BasicAuthMiddleware
        app = BasicAuthMiddleware(original_app)
    """

    def __init__(self, app, realm: str = "CdE Dashboard"):
        self.app = app
        self.realm = realm
        _load_env_file()
        self.username = os.environ.get("DASHBOARD_USER", "")
        self.password = os.environ.get("DASHBOARD_PASS", "")
        if not self.username or not self.password:
            raise RuntimeError(
                "DASHBOARD_USER and DASHBOARD_PASS must be set. "
                "Create a .env file in the project root or set environment variables."
            )

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if self._is_authorized(auth_header):
            await self.app(scope, receive, send)
        else:
            if scope["type"] == "websocket":
                # For WebSocket, reject the connection
                await send({"type": "websocket.close", "code": 4003})
            else:
                await self._send_401(send)

    def _is_authorized(self, auth_header: str) -> bool:
        if not auth_header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, _, password = decoded.partition(":")
            return (
                _constant_time_compare(username, self.username)
                and _constant_time_compare(password, self.password)
            )
        except Exception:
            return False

    async def _send_401(self, send):
        body = b"<html><body><h1>401 Unauthorized</h1><p>Valid credentials required.</p></body></html>"
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                [b"www-authenticate", f'Basic realm="{self.realm}"'.encode()],
                [b"content-type", b"text/html; charset=utf-8"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
