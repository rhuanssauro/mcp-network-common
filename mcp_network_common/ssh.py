"""Shared SSH connection factory using Scrapli."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

from scrapli import AsyncScrapli
from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
    ScrapliTimeout,
)

from mcp_network_common.response import error_response

logger = logging.getLogger(__name__)


async def create_scrapli_conn(
    device: dict[str, Any],
    *,
    platform: str,
    port_key: str = "port",
    timeout_socket: int = 30,
    timeout_transport: int = 30,
    timeout_ops: int = 60,
) -> AsyncScrapli:
    """Create and open an AsyncScrapli connection.

    Args:
        device: Device dict with host, username, password, and port keys.
        platform: Scrapli platform string (e.g. "cisco_iosxe", "fortinet_fortios").
        port_key: Key in *device* dict for the SSH port (default "port").
        timeout_socket: Socket timeout in seconds.
        timeout_transport: Transport timeout in seconds.
        timeout_ops: Operations timeout in seconds.
    """
    conn = AsyncScrapli(
        host=device["host"],
        auth_username=device.get("username", "admin"),
        auth_password=device.get("password", ""),
        platform=platform,
        port=device.get(port_key, 22),
        auth_strict_key=False,
        transport="asyncssh",
        timeout_socket=timeout_socket,
        timeout_transport=timeout_transport,
        timeout_ops=timeout_ops,
    )
    await conn.open()
    return conn


def handle_ssh_errors(func: Callable) -> Callable:
    """Decorator that catches Scrapli exceptions and returns JSON error responses.

    Expects the wrapped function to accept ``device_name`` as its first argument.

    Usage::

        @mcp.tool()
        @handle_ssh_errors
        async def my_tool(device_name: str, ...) -> str:
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        # Extract device_name from first positional arg or kwargs
        device_name = kwargs.get("device_name") or (args[0] if args else "unknown")
        try:
            return await func(*args, **kwargs)
        except ScrapliAuthenticationFailed as e:
            logger.error("Auth failed on %s: %s", device_name, e)
            return error_response(f"Authentication failed: {e}")
        except (ScrapliConnectionError, ScrapliTimeout) as e:
            logger.error("Connection error on %s: %s", device_name, e)
            return error_response(f"Connection error: {e}")
        except ValueError as e:
            return error_response(str(e))
        except Exception as e:
            logger.error("Error on %s: %s", device_name, e, exc_info=True)
            return error_response(str(e))

    return wrapper
