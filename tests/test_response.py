"""Tests for response module."""

from __future__ import annotations

import json

from mcp_network_common.response import error_response, json_dumps, ok_response


class TestJsonDumps:
    def test_basic_dict(self):
        result = json_dumps({"key": "value"})
        assert json.loads(result) == {"key": "value"}

    def test_indent_is_two(self):
        result = json_dumps({"a": 1})
        assert "  " in result

    def test_default_str_for_non_serializable(self):
        result = json_dumps({"obj": object()})
        parsed = json.loads(result)
        assert isinstance(parsed["obj"], str)


class TestOkResponse:
    def test_includes_status_ok(self):
        result = json.loads(ok_response(device="sw01"))
        assert result["status"] == "ok"
        assert result["device"] == "sw01"

    def test_multiple_fields(self):
        result = json.loads(ok_response(device="r01", command="show ver", output="..."))
        assert result["status"] == "ok"
        assert result["device"] == "r01"
        assert result["command"] == "show ver"

    def test_no_extra_fields(self):
        result = json.loads(ok_response())
        assert result == {"status": "ok"}


class TestErrorResponse:
    def test_string_error(self):
        result = json.loads(error_response("something failed"))
        assert result["status"] == "error"
        assert result["error"] == "something failed"

    def test_exception_error(self):
        result = json.loads(error_response(ValueError("bad value")))
        assert result["status"] == "error"
        assert "bad value" in result["error"]
