"""Tests for the check_connection plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.plugins.check_connection.api import CheckConnectionApi


def _make_context():
    mock_client = MagicMock()
    return {"get_config_client": lambda: mock_client, "format": "json", "_client": mock_client}


class TestCheckConnectionApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_check_source_posts_correct_body(self):
        self.client.request.return_value = {"status": "succeeded"}
        api = CheckConnectionApi(self.client)
        result = api.check_source("src-1")
        self.client.request.assert_called_once_with(
            "POST", "sources/check_connection",
            body={"sourceId": "src-1"},
        )
        self.assertEqual(result["status"], "succeeded")

    def test_check_destination_posts_correct_body(self):
        self.client.request.return_value = {"status": "succeeded"}
        api = CheckConnectionApi(self.client)
        result = api.check_destination("dst-1")
        self.client.request.assert_called_once_with(
            "POST", "destinations/check_connection",
            body={"destinationId": "dst-1"},
        )
        self.assertEqual(result["status"], "succeeded")

    def test_check_source_failed_response(self):
        self.client.request.return_value = {"status": "failed", "message": "Connection refused"}
        api = CheckConnectionApi(self.client)
        result = api.check_source("src-bad")
        self.assertEqual(result["status"], "failed")

    def test_check_destination_failed_response(self):
        self.client.request.return_value = {"status": "failed", "message": "Timeout"}
        api = CheckConnectionApi(self.client)
        result = api.check_destination("dst-bad")
        self.assertEqual(result["status"], "failed")


class TestCheckConnectionPluginRegistration(unittest.TestCase):
    def setUp(self):
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        import airbyte_api_cli.plugins.check_connection
        importlib.reload(airbyte_api_cli.plugins.check_connection)
        plugin = Registry.instance().get_plugin("check_connection")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "check_connection")

    def test_register_adds_subparser(self):
        import argparse
        from airbyte_api_cli.plugins.check_connection.commands import register_commands

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd")
        context = {"get_config_client": lambda: MagicMock(), "format": "json"}
        register_commands(subparsers, context)
        args = parser.parse_args(["check_connection", "source", "--id", "src-1"])
        self.assertTrue(hasattr(args, "handler"))
        self.assertEqual(args.source_id, "src-1")


class TestCheckConnectionCommands(unittest.TestCase):
    def test_handle_source(self):
        from airbyte_api_cli.plugins.check_connection.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "source"
        args.source_id = "src-1"

        with patch("airbyte_api_cli.plugins.check_connection.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_destination(self):
        from airbyte_api_cli.plugins.check_connection.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "destination"
        args.destination_id = "dst-1"

        with patch("airbyte_api_cli.plugins.check_connection.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_no_action_returns_error(self):
        from airbyte_api_cli.plugins.check_connection.commands import _handle

        ctx = _make_context()
        args = MagicMock()
        args.action = None

        with patch("airbyte_api_cli.plugins.check_connection.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_unknown_action_returns_error(self):
        from airbyte_api_cli.plugins.check_connection.commands import _handle

        ctx = _make_context()
        args = MagicMock()
        args.action = "unknown"

        with patch("airbyte_api_cli.plugins.check_connection.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_source_passes_format_to_output(self):
        from airbyte_api_cli.plugins.check_connection.commands import _handle

        ctx = _make_context()
        ctx["format"] = "table"
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "source"
        args.source_id = "src-2"

        with patch("airbyte_api_cli.plugins.check_connection.commands.output") as mock_out:
            _handle(args, ctx)
        mock_out.assert_called_once_with({"status": "succeeded"}, "table")


if __name__ == "__main__":
    unittest.main()
