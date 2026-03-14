"""Tests for the web_backend plugin."""

from __future__ import annotations

import argparse
import importlib
import unittest
from unittest.mock import MagicMock

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.web_backend.api import WebBackendApi
from airbyte_api_cli.plugins.web_backend.commands import _handle, register_commands


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestWebBackendApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=HttpClient)
        self.api = WebBackendApi(self.client)

    def test_list_connections_calls_correct_endpoint(self):
        self.client.request.return_value = {"connections": [{"connectionId": "c1"}]}
        result = self.api.list_connections("ws1")
        self.client.request.assert_called_once_with(
            "POST", "web_backend/connections/list",
            body={"workspaceId": "ws1"},
        )
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["connectionId"], "c1")

    def test_list_connections_missing_key_returns_empty(self):
        self.client.request.return_value = {}
        result = self.api.list_connections("ws1")
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data, [])

    def test_get_connection_calls_correct_endpoint(self):
        self.client.request.return_value = {"connectionId": "c1", "name": "My Conn"}
        result = self.api.get_connection("c1")
        self.client.request.assert_called_once_with(
            "POST", "web_backend/connections/get",
            body={"connectionId": "c1", "withRefreshedCatalog": False},
        )
        self.assertEqual(result["connectionId"], "c1")

    def test_get_connection_with_refreshed_catalog(self):
        self.client.request.return_value = {"connectionId": "c1"}
        self.api.get_connection("c1", with_refreshed_catalog=True)
        call_body = self.client.request.call_args[1]["body"]
        self.assertTrue(call_body["withRefreshedCatalog"])

    def test_check_updates_calls_correct_endpoint(self):
        self.client.request.return_value = {"destinationDefinitions": [], "sourceDefinitions": []}
        result = self.api.check_updates()
        self.client.request.assert_called_once_with(
            "POST", "web_backend/check_updates", body={}
        )
        self.assertIn("destinationDefinitions", result)

    def test_workspace_state_calls_correct_endpoint(self):
        self.client.request.return_value = {"hasConnections": True}
        result = self.api.workspace_state("ws1")
        self.client.request.assert_called_once_with(
            "POST", "web_backend/workspace/state",
            body={"workspaceId": "ws1"},
        )
        self.assertTrue(result["hasConnections"])


# ---------------------------------------------------------------------------
# Command registration tests
# ---------------------------------------------------------------------------


class TestWebBackendCommandRegistration(unittest.TestCase):
    def _make_parser(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        return parser

    def test_list_command_parses_workspace_id(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "list", "--workspace-id", "ws1"])
        self.assertEqual(args.action, "list")
        self.assertEqual(args.workspace_id, "ws1")

    def test_get_command_parses_connection_id(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "get", "--id", "c1"])
        self.assertEqual(args.action, "get")
        self.assertEqual(args.connection_id, "c1")

    def test_get_command_with_refreshed_catalog_default_false(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "get", "--id", "c1"])
        self.assertFalse(args.with_refreshed_catalog)

    def test_get_command_with_refreshed_catalog_flag(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "get", "--id", "c1", "--with-refreshed-catalog"])
        self.assertTrue(args.with_refreshed_catalog)

    def test_check_updates_needs_no_args(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "check-updates"])
        self.assertEqual(args.action, "check-updates")

    def test_workspace_state_parses_workspace_id(self):
        parser = self._make_parser()
        args = parser.parse_args(["web_backend", "workspace-state", "--workspace-id", "ws1"])
        self.assertEqual(args.action, "workspace-state")
        self.assertEqual(args.workspace_id, "ws1")


# ---------------------------------------------------------------------------
# Command handler tests
# ---------------------------------------------------------------------------


class TestWebBackendHandle(unittest.TestCase):
    def test_list_calls_api_and_returns_0(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"connections": [{"connectionId": "c1"}]}
        args = argparse.Namespace(action="list", workspace_id="ws1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "web_backend/connections/list",
            body={"workspaceId": "ws1"},
        )

    def test_get_calls_api_and_returns_0(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"connectionId": "c1"}
        args = argparse.Namespace(action="get", connection_id="c1", with_refreshed_catalog=False)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "web_backend/connections/get",
            body={"connectionId": "c1", "withRefreshedCatalog": False},
        )

    def test_get_passes_with_refreshed_catalog_true(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"connectionId": "c1"}
        args = argparse.Namespace(action="get", connection_id="c1", with_refreshed_catalog=True)
        _handle(args, _ctx(mock_client))
        call_body = mock_client.request.call_args[1]["body"]
        self.assertTrue(call_body["withRefreshedCatalog"])

    def test_check_updates_calls_api_and_returns_0(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"destinationDefinitions": []}
        args = argparse.Namespace(action="check-updates")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "web_backend/check_updates", body={}
        )

    def test_workspace_state_calls_api_and_returns_0(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"hasConnections": False}
        args = argparse.Namespace(action="workspace-state", workspace_id="ws1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "web_backend/workspace/state",
            body={"workspaceId": "ws1"},
        )

    def test_no_action_returns_1(self):
        mock_client = MagicMock()
        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 1)
        mock_client.request.assert_not_called()


# ---------------------------------------------------------------------------
# Plugin registration test
# ---------------------------------------------------------------------------


class TestWebBackendPluginRegistration(unittest.TestCase):
    def setUp(self):
        from airbyte_api_cli.core.registry import Registry
        Registry.reset()

    def test_plugin_registers_on_import(self):
        from airbyte_api_cli.core.registry import Registry
        import airbyte_api_cli.plugins.web_backend
        importlib.reload(airbyte_api_cli.plugins.web_backend)
        plugin = Registry.instance().get_plugin("web_backend")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "web_backend")


if __name__ == "__main__":
    unittest.main()
