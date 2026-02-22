"""Tests for inventory module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from mcp_network_common.inventory import get_device, load_inventory


class TestLoadInventory:
    def test_load_from_json_file(self, tmp_path):
        devices_file = tmp_path / "devices.json"
        devices_file.write_text(
            json.dumps(
                {
                    "sw01": {
                        "host": "10.0.0.1",
                        "username": "admin",
                        "password": "pass",
                    },
                    "sw02": {
                        "host": "10.0.0.2",
                        "username": "admin",
                        "password": "pass",
                    },
                }
            )
        )

        devices = {}
        os.environ["TEST_DEVICES_JSON"] = str(devices_file)
        try:
            load_inventory("TEST", devices)
        finally:
            del os.environ["TEST_DEVICES_JSON"]

        assert len(devices) == 2
        assert devices["sw01"]["host"] == "10.0.0.1"

    def test_load_single_device_from_env(self):
        devices = {}
        env = {
            "SINGLE_HOST": "192.168.1.1",
            "SINGLE_USER": "root",
            "SINGLE_PASS": "secret",
            "SINGLE_PORT": "2222",
        }
        for k, v in env.items():
            os.environ[k] = v
        try:
            load_inventory("SINGLE", devices)
        finally:
            for k in env:
                del os.environ[k]

        assert "default" in devices
        assert devices["default"]["host"] == "192.168.1.1"
        assert devices["default"]["username"] == "root"
        assert devices["default"]["port"] == 2222

    def test_default_fields_merged(self):
        devices = {}
        os.environ["DF_HOST"] = "10.0.0.5"
        try:
            load_inventory("DF", devices, default_fields={"platform": "iosxe"})
        finally:
            del os.environ["DF_HOST"]

        assert devices["default"]["platform"] == "iosxe"

    def test_no_env_vars_set(self):
        devices = {}
        load_inventory("NONEXISTENT_PREFIX_XYZ", devices)
        assert len(devices) == 0

    def test_json_file_takes_precedence(self, tmp_path):
        devices_file = tmp_path / "devices.json"
        devices_file.write_text(
            json.dumps(
                {
                    "from_file": {"host": "1.1.1.1"},
                }
            )
        )

        os.environ["PRIO_DEVICES_JSON"] = str(devices_file)
        os.environ["PRIO_HOST"] = "2.2.2.2"
        devices = {}
        try:
            load_inventory("PRIO", devices)
        finally:
            del os.environ["PRIO_DEVICES_JSON"]
            del os.environ["PRIO_HOST"]

        assert "from_file" in devices
        assert "default" not in devices


class TestGetDevice:
    def test_get_existing_device(self):
        devices = {"sw01": {"host": "10.0.0.1"}}
        result = get_device("sw01", devices)
        assert result["host"] == "10.0.0.1"

    def test_get_missing_device_raises(self):
        devices = {"sw01": {"host": "10.0.0.1"}}
        with pytest.raises(ValueError, match="not in inventory"):
            get_device("sw99", devices)

    def test_error_lists_available_devices(self):
        devices = {"a": {}, "b": {}, "c": {}}
        with pytest.raises(ValueError, match="Available"):
            get_device("z", devices)
