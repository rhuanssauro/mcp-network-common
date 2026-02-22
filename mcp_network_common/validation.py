"""Shared command validation for MCP servers."""

from __future__ import annotations

import re
from typing import Sequence


class CommandValidator:
    """Base validator for network device commands.

    Subclass and override class attributes to customise per vendor.

    Attributes:
        readonly_prefixes: Tuple of allowed read-only command prefixes.
        show_block_words: Set of words that block show/read-only commands.
        config_blocked_patterns: List of (regex, label) tuples for config commands.
        block_pipe_redirect: Whether to block ``|``, ``>``, ``<`` in read-only
            commands.
    """

    readonly_prefixes: tuple[str, ...] = ("show",)
    show_block_words: set[str] = {
        "copy",
        "delete",
        "erase",
        "reload",
        "write",
        "configure",
        "conf",
    }
    config_blocked_patterns: list[tuple[str, str]] = [
        (r"\bwrite\s+erase\b", "write erase"),
        (r"^\s*erase\b", "erase"),
        (r"\breload\b", "reload"),
        (r"\bdelete\b", "delete"),
        (r"\bformat\b", "format"),
    ]
    block_pipe_redirect: bool = True

    def validate_readonly(self, command: str) -> str | None:
        """Validate a read-only command. Return error message or ``None``."""
        cmd = command.strip().lower()
        if not any(cmd.startswith(p) for p in self.readonly_prefixes):
            allowed = ", ".join(self.readonly_prefixes)
            return f"Only read-only commands allowed ({allowed}). Got: '{command}'"
        tokens = re.findall(r"[a-zA-Z0-9_-]+", cmd)
        for t in tokens:
            if t in self.show_block_words:
                return f"Blocked term '{t}' in command."
        if self.block_pipe_redirect and any(c in cmd for c in ["|", ">", "<"]):
            return "Pipe/redirect characters not allowed."
        return None

    def validate_config(self, lines: Sequence[str]) -> str | None:
        """Validate configuration lines. Return error message or ``None``."""
        joined = "\n".join(lines).lower()
        for pattern, label in self.config_blocked_patterns:
            if re.search(pattern, joined, flags=re.MULTILINE):
                return f"Dangerous command blocked: '{label}'"
        return None
