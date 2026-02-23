"""Tests for SSH module."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from mcp_network_common.ssh import create_scrapli_conn, handle_ssh_errors


class TestHandleSshErrors:
    @pytest.mark.asyncio
    async def test_passes_through_on_success(self):
        @handle_ssh_errors
        async def my_tool(device_name: str) -> str:
            return '{"status": "ok"}'

        result = await my_tool("sw01")
        assert json.loads(result)["status"] == "ok"

    @pytest.mark.asyncio
    async def test_catches_value_error(self):
        @handle_ssh_errors
        async def my_tool(device_name: str) -> str:
            raise ValueError("Device not found")

        result = await my_tool("sw01")
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "not found" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_catches_generic_exception(self):
        @handle_ssh_errors
        async def my_tool(device_name: str) -> str:
            raise RuntimeError("unexpected")

        result = await my_tool("sw01")
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "unexpected" in parsed["error"]


class TestCreateScrapliConn:
    @pytest.mark.asyncio
    async def test_creates_connection_with_correct_params(self):
        device = {
            "host": "10.0.0.1",
            "username": "admin",
            "password": "secret",
            "port": 22,
        }

        with patch("mcp_network_common.ssh.AsyncScrapli") as MockScrapli:
            mock_conn = AsyncMock()
            MockScrapli.return_value = mock_conn

            await create_scrapli_conn(device, platform="cisco_iosxe")

            MockScrapli.assert_called_once()
            call_kwargs = MockScrapli.call_args[1]
            assert call_kwargs["host"] == "10.0.0.1"
            assert call_kwargs["platform"] == "cisco_iosxe"
            assert call_kwargs["auth_strict_key"] is False
            assert call_kwargs["transport"] == "asyncssh"
            mock_conn.open.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_custom_port_key(self):
        device = {"host": "10.0.0.1", "ssh_port": 2222}

        with patch("mcp_network_common.ssh.AsyncScrapli") as MockScrapli:
            mock_conn = AsyncMock()
            MockScrapli.return_value = mock_conn

            await create_scrapli_conn(device, platform="linux", port_key="ssh_port")

            call_kwargs = MockScrapli.call_args[1]
            assert call_kwargs["port"] == 2222
