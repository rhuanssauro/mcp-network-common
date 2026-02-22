"""Shared JSON response formatting for MCP servers."""

from __future__ import annotations

import json
from typing import Any


def json_dumps(data: Any) -> str:
    """Serialize *data* to a JSON string with indent=2 and default=str."""
    return json.dumps(data, indent=2, default=str)


def ok_response(**fields: Any) -> str:
    """Return a JSON success response.

    Example::

        ok_response(device="sw01", output="...")
        # '{"status": "ok", "device": "sw01", "output": "..."}'
    """
    return json_dumps({"status": "ok", **fields})


def error_response(error: str | Exception) -> str:
    """Return a JSON error response.

    Example::

        error_response("Device not found")
        error_response(some_exception)
    """
    return json_dumps({"status": "error", "error": str(error)})
