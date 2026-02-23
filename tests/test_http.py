"""Tests for HTTP module."""

from __future__ import annotations

import json
import os

import pytest

from mcp_network_common.http import create_http_client, handle_http_errors


class TestCreateHttpClient:
    def test_returns_async_client(self):
        client = create_http_client()
        assert hasattr(client, "get")
        assert hasattr(client, "post")

    def test_with_base_url(self):
        client = create_http_client(base_url="https://example.com")
        assert str(client.base_url) == "https://example.com"

    def test_tls_verify_false_by_default(self):
        # MCP_TLS_VERIFY defaults to "false"
        os.environ.pop("MCP_TLS_VERIFY", None)
        client = create_http_client()
        # Should not raise — just verify it creates
        assert client is not None

    def test_tls_verify_true(self):
        os.environ["MCP_TLS_VERIFY"] = "true"
        try:
            client = create_http_client()
            assert client is not None
        finally:
            del os.environ["MCP_TLS_VERIFY"]


class TestHandleHttpErrors:
    @pytest.mark.asyncio
    async def test_passes_through_on_success(self):
        @handle_http_errors
        async def my_tool(device_name: str) -> str:
            return '{"status": "ok"}'

        result = await my_tool("fw01")
        assert json.loads(result)["status"] == "ok"

    @pytest.mark.asyncio
    async def test_catches_value_error(self):
        @handle_http_errors
        async def my_tool(device_name: str) -> str:
            raise ValueError("Device not found")

        result = await my_tool("fw01")
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "not found" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_catches_generic_exception(self):
        @handle_http_errors
        async def my_tool(device_name: str) -> str:
            raise RuntimeError("unexpected")

        result = await my_tool("fw01")
        parsed = json.loads(result)
        assert parsed["status"] == "error"
