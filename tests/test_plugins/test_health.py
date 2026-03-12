"""Tests for the health plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from airbyte_cli.core.registry import Registry


class TestHealthCommand(unittest.TestCase):
    def setUp(self):
        Registry.reset()
        import importlib
        import airbyte_cli.plugins.health as _mod
        importlib.reload(_mod)

    def _make_context(self, health_response):
        mock_client = MagicMock()
        mock_client.request.return_value = health_response
        return {"get_client": lambda: mock_client, "format": "json"}, mock_client

    def test_health_calls_get_health(self):
        import argparse
        from airbyte_cli.plugins.health.commands import _handle

        context, mock_client = self._make_context({"available": True})
        args = argparse.Namespace()
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("GET", "health")

    def test_health_prints_output(self):
        import argparse
        from airbyte_cli.plugins.health.commands import _handle

        with patch("airbyte_cli.plugins.health.commands.output") as mock_output:
            context, mock_client = self._make_context({"available": True})
            rc = _handle(argparse.Namespace(), context)

        self.assertEqual(rc, 0)
        mock_output.assert_called_once_with({"available": True}, "json")

    def test_health_empty_response(self):
        import argparse
        from airbyte_cli.plugins.health.commands import _handle

        context, mock_client = self._make_context({})
        rc = _handle(argparse.Namespace(), context)
        self.assertEqual(rc, 0)

    def test_plugin_registered(self):
        from airbyte_cli.plugins.health import register
        Registry.reset()
        register()
        self.assertIn("health", Registry.instance().all_plugins())

    def test_register_commands_adds_parser(self):
        import argparse
        from airbyte_cli.plugins.health.commands import register_commands

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd")
        context = {"get_client": lambda: MagicMock(), "format": "json"}
        register_commands(subparsers, context)
        # Verify "health" subcommand is parseable
        args = parser.parse_args(["health"])
        self.assertTrue(hasattr(args, "handler"))


if __name__ == "__main__":
    unittest.main()
