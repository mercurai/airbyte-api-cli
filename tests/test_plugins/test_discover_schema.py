"""Tests for the discover_schema plugin."""

from __future__ import annotations

import argparse
import json
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.plugins.discover_schema.api import DiscoverSchemaApi
from airbyte_api_cli.plugins.discover_schema.commands import register_commands, _handle


def _make_response(body: dict, status: int = 200) -> MagicMock:
    raw = json.dumps(body).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = raw
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


class TestDiscoverSchemaApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = DiscoverSchemaApi(self.client)

    def test_discover_builds_correct_body(self):
        self.client.request.return_value = {"catalog": {}}
        self.api.discover("src-1")
        self.client.request.assert_called_once_with(
            "POST",
            "sources/discover_schema",
            body={"sourceId": "src-1"},
        )

    def test_discover_disable_cache_adds_flag(self):
        self.client.request.return_value = {"catalog": {}}
        self.api.discover("src-2", disable_cache=True)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["sourceId"], "src-2")
        self.assertTrue(call_body["disable_cache"])

    def test_discover_disable_cache_false_omits_flag(self):
        self.client.request.return_value = {"catalog": {}}
        self.api.discover("src-3", disable_cache=False)
        call_body = self.client.request.call_args[1]["body"]
        self.assertNotIn("disable_cache", call_body)

    def test_discover_returns_response(self):
        payload = {"catalog": {"streams": [{"name": "users"}]}}
        self.client.request.return_value = payload
        result = self.api.discover("src-1")
        self.assertEqual(result, payload)


class TestDiscoverSchemaCommands(unittest.TestCase):
    def test_command_parses_source_id(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["discover_schema", "--source-id", "src-99"])
        self.assertEqual(args.source_id, "src-99")

    def test_command_disable_cache_default_false(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["discover_schema", "--source-id", "src-1"])
        self.assertFalse(args.disable_cache)

    def test_command_disable_cache_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["discover_schema", "--source-id", "src-1", "--disable-cache"])
        self.assertTrue(args.disable_cache)

    def test_handle_calls_api_and_returns_0(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"catalog": {}}
        args = argparse.Namespace(source_id="src-1", disable_cache=False)
        with patch("airbyte_api_cli.plugins.discover_schema.commands.output"):
            result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "sources/discover_schema",
            body={"sourceId": "src-1"},
        )

    def test_handle_passes_result_to_output(self):
        mock_client = MagicMock()
        payload = {"catalog": {"streams": []}}
        mock_client.request.return_value = payload
        args = argparse.Namespace(source_id="src-1", disable_cache=False)
        with patch("airbyte_api_cli.plugins.discover_schema.commands.output") as mock_out:
            _handle(args, _ctx(mock_client))
        call_args = mock_out.call_args
        self.assertEqual(call_args[0][0], payload)

    def test_handle_disable_cache_forwarded(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(source_id="src-2", disable_cache=True)
        with patch("airbyte_api_cli.plugins.discover_schema.commands.output"):
            _handle(args, _ctx(mock_client))
        call_body = mock_client.request.call_args[1]["body"]
        self.assertTrue(call_body["disable_cache"])


class TestDiscoverSchemaRegistration(unittest.TestCase):
    def setUp(self):
        from airbyte_api_cli.core.registry import Registry
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        from airbyte_api_cli.core.registry import Registry
        import airbyte_api_cli.plugins.discover_schema
        importlib.reload(airbyte_api_cli.plugins.discover_schema)
        plugin = Registry.instance().get_plugin("discover_schema")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "discover_schema")


if __name__ == "__main__":
    unittest.main()
