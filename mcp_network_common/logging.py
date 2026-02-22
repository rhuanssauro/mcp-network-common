"""Shared logging setup for MCP servers."""

from __future__ import annotations

import logging
import sys


def setup_logger(name: str, *, level: int = logging.INFO) -> logging.Logger:
    """Configure logging and return a named logger.

    Sets up basicConfig with stderr output and a consistent format string.
    Safe to call multiple times (basicConfig is idempotent after first call).

    Args:
        name: Logger name (e.g. "CiscoMCPServer").
        level: Logging level, defaults to INFO.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    return logging.getLogger(name)
