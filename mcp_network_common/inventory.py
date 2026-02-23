"""Shared device inventory loading for MCP servers."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def load_inventory(
    prefix: str,
    devices: dict[str, dict[str, Any]],
    *,
    default_fields: dict[str, Any] | None = None,
) -> None:
    """Load device inventory from env vars into *devices* dict (mutated in-place).

    Looks for ``{PREFIX}_DEVICES_JSON`` first (path to a JSON file).
    Falls back to a single device from ``{PREFIX}_HOST``, ``{PREFIX}_USER``,
    ``{PREFIX}_PASS``, ``{PREFIX}_PORT``.

    Args:
        prefix: Environment variable prefix (e.g. "CISCO", "FORTINET").
        devices: Mutable dict to populate with device entries.
        default_fields: Extra key/value pairs merged into the single-device
            fallback entry (e.g. ``{"platform": "iosxe"}``).
    """
    json_path = os.getenv(f"{prefix}_DEVICES_JSON")
    if json_path and os.path.exists(json_path):
        with open(json_path) as f:
            devices.update(json.load(f))
        logger.info("Loaded %d devices from %s", len(devices), json_path)
        return

    host = os.getenv(f"{prefix}_HOST")
    if host:
        entry: dict[str, Any] = {
            "host": host,
            "username": os.getenv(f"{prefix}_USER", "admin"),
            "password": os.getenv(f"{prefix}_PASS", ""),
            "port": int(os.getenv(f"{prefix}_PORT", "22")),
        }
        if default_fields:
            entry.update(default_fields)
        devices["default"] = entry
        logger.info("Loaded single device: %s", host)


def get_device(
    device_name: str,
    devices: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Retrieve a device from *devices* by name, or raise ``ValueError``.

    Args:
        device_name: Key to look up in the devices dict.
        devices: The inventory dict (from ``load_inventory``).
    """
    if device_name not in devices:
        raise ValueError(
            f"Device '{device_name}' not in inventory. Available: {list(devices.keys())}"
        )
    return devices[device_name]
