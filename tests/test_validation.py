"""Tests for validation module."""

from __future__ import annotations

from mcp_network_common.validation import CommandValidator


class TestCommandValidator:
    def setup_method(self):
        self.v = CommandValidator()

    def test_valid_show_command(self):
        assert self.v.validate_readonly("show ip route") is None

    def test_rejects_non_show_command(self):
        err = self.v.validate_readonly("configure terminal")
        assert err is not None
        assert "read-only" in err.lower()

    def test_blocks_dangerous_word_in_show(self):
        err = self.v.validate_readonly("show delete flash:")
        assert err is not None
        assert "delete" in err.lower()

    def test_blocks_pipe_redirect(self):
        err = self.v.validate_readonly("show running | include interface")
        assert err is not None
        assert "pipe" in err.lower() or "redirect" in err.lower()

    def test_valid_config_lines(self):
        lines = ["interface GigabitEthernet0/1", "ip address 10.0.0.1 255.255.255.0"]
        assert self.v.validate_config(lines) is None

    def test_blocks_write_erase(self):
        lines = ["write erase"]
        err = self.v.validate_config(lines)
        assert err is not None
        assert "write erase" in err.lower()

    def test_blocks_reload(self):
        lines = ["reload"]
        err = self.v.validate_config(lines)
        assert err is not None

    def test_blocks_delete(self):
        lines = ["delete flash:startup-config"]
        err = self.v.validate_config(lines)
        assert err is not None


class TestCustomValidator:
    def test_custom_readonly_prefixes(self):
        class FortiValidator(CommandValidator):
            readonly_prefixes = ("get", "show", "diagnose")

        v = FortiValidator()
        assert v.validate_readonly("get system status") is None
        assert v.validate_readonly("diagnose sniffer packet") is None

    def test_custom_block_words(self):
        class FortiValidator(CommandValidator):
            show_block_words = {"reboot", "shutdown"}

        v = FortiValidator()
        err = v.validate_readonly("show reboot status")
        assert err is not None

    def test_custom_config_patterns(self):
        class FortiValidator(CommandValidator):
            config_blocked_patterns = [
                (r"\bexecute\s+reboot\b", "execute reboot"),
                (r"\bexecute\s+factoryreset\b", "execute factoryreset"),
            ]

        v = FortiValidator()
        err = v.validate_config(["execute reboot"])
        assert err is not None
        assert v.validate_config(["config system global"]) is None
