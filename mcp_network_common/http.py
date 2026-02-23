"""Shared HTTP client factory for MCP servers."""

from __future__ import annotations

import functools
import logging
import os
import ssl
from collections.abc import Callable
from typing import Any

import httpx

from mcp_network_common.response import error_response

logger = logging.getLogger(__name__)


def _tls_verify() -> ssl.SSLContext | bool:
    """Return an SSL context based on ``MCP_TLS_VERIFY`` env var.

    When ``MCP_TLS_VERIFY`` is ``"false"`` (default), returns an unverified
    SSL context that skips hostname and certificate checks — suitable for
    self-signed lab devices.
    """
    if os.getenv("MCP_TLS_VERIFY", "false").lower() != "false":
        return ssl.create_default_context()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def create_http_client(
    *,
    base_url: str = "",
    timeout: float = 30.0,
    auth: httpx.Auth | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.AsyncClient:
    """Create an ``httpx.AsyncClient`` with shared TLS and timeout config.

    Args:
        base_url: Optional base URL for all requests.
        timeout: Request timeout in seconds.
        auth: Optional httpx auth (e.g. ``httpx.BasicAuth``).
        headers: Extra default headers.
    """
    return httpx.AsyncClient(
        base_url=base_url,
        verify=_tls_verify(),
        timeout=httpx.Timeout(timeout),
        auth=auth,
        headers=headers or {},
    )


def handle_http_errors(func: Callable) -> Callable:
    """Decorator that catches httpx exceptions and returns JSON error responses.

    Expects the wrapped function to accept ``device_name`` as its first argument.

    Usage::

        @mcp.tool()
        @handle_http_errors
        async def my_api_tool(device_name: str, ...) -> str:
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        device_name = kwargs.get("device_name") or (args[0] if args else "unknown")
        try:
            return await func(*args, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("Connection error on %s: %s", device_name, e)
            return error_response(f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error on %s: %s", device_name, e)
            return error_response(f"HTTP {e.response.status_code}: {e}")
        except ValueError as e:
            return error_response(str(e))
        except Exception as e:
            logger.error("HTTP error on %s: %s", device_name, e, exc_info=True)
            return error_response(str(e))

    return wrapper
