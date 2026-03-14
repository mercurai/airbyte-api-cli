"""Tests for the state plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestStateApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        from airbyte_api_cli.plugins.state.api import StateApi
        self.api = StateApi(self.client)

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {"connectionId": "conn_1", "state": []}
        result = self.api.get("conn_1")
        self.client.request.assert_called_once_with(
            "POST", "state/get",
            body={"connectionId": "conn_1"},
        )
        self.assertEqual(result["connectionId"], "conn_1")

    def test_get_returns_response_as_is(self):
        expected = {"connectionId": "conn_2", "state": [{"type": "GLOBAL"}]}
        self.client.request.return_value = expected
        result = self.api.get("conn_2")
        self.assertEqual(result, expected)

    def test_create_or_update_calls_correct_endpoint(self):
        state_payload = {"type": "GLOBAL", "globalState": {"sharedState": {}}}
        self.client.request.return_value = {"connectionId": "conn_1", "connectionState": state_payload}
        result = self.api.create_or_update("conn_1", state_payload)
        self.client.request.assert_called_once_with(
            "POST", "state/create_or_update",
            body={"connectionId": "conn_1", "connectionState": state_payload},
        )
        self.assertEqual(result["connectionId"], "conn_1")

    def test_create_or_update_passes_state_as_connection_state(self):
        state_payload = {"type": "STREAM", "streamState": []}
        self.client.request.return_value = {}
        self.api.create_or_update("conn_3", state_payload)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["connectionState"], state_payload)
        self.assertEqual(call_body["connectionId"], "conn_3")

    def test_create_or_update_empty_state(self):
        self.client.request.return_value = {}
        self.api.create_or_update("conn_4", {})
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["connectionState"], {})


# ---------------------------------------------------------------------------
# Command parser tests
# ---------------------------------------------------------------------------


class TestStateCommandParsing(unittest.TestCase):
    def _make_parser(self):
        from airbyte_api_cli.plugins.state.commands import register_commands
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        return parser

    def test_get_command_parses_connection_id(self):
        parser = self._make_parser()
        args = parser.parse_args(["state", "get", "--connection-id", "conn_1"])
        self.assertEqual(args.action, "get")
        self.assertEqual(args.connection_id, "conn_1")

    def test_set_command_parses_connection_id_and_state(self):
        parser = self._make_parser()
        args = parser.parse_args([
            "state", "set",
            "--connection-id", "conn_1",
            "--state", '{"type":"GLOBAL"}',
        ])
        self.assertEqual(args.action, "set")
        self.assertEqual(args.connection_id, "conn_1")
        self.assertEqual(args.state, '{"type":"GLOBAL"}')

    def test_get_requires_connection_id(self):
        parser = self._make_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["state", "get"])

    def test_set_requires_connection_id(self):
        parser = self._make_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["state", "set", "--state", '{}'])

    def test_set_requires_state(self):
        parser = self._make_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["state", "set", "--connection-id", "conn_1"])


# ---------------------------------------------------------------------------
# Command handler tests
# ---------------------------------------------------------------------------


class TestStateCommandHandler(unittest.TestCase):
    def test_get_action_calls_api_and_returns_0(self):
        from airbyte_api_cli.plugins.state.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"connectionId": "conn_1", "state": []}
        args = argparse.Namespace(action="get", connection_id="conn_1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "state/get",
            body={"connectionId": "conn_1"},
        )

    def test_set_action_uses_resolve_json_arg(self):
        from airbyte_api_cli.plugins.state.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        state_json = '{"type":"GLOBAL","globalState":{}}'
        args = argparse.Namespace(action="set", connection_id="conn_1", state=state_json)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["connectionState"], {"type": "GLOBAL", "globalState": {}})

    def test_set_action_parses_state_from_inline_json(self):
        from airbyte_api_cli.plugins.state.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(
            action="set",
            connection_id="conn_2",
            state='{"type":"STREAM","streamState":[]}',
        )
        _handle(args, _ctx(mock_client))
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["connectionState"]["type"], "STREAM")

    def test_no_action_returns_1(self):
        from airbyte_api_cli.plugins.state.commands import _handle

        mock_client = MagicMock()
        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 1)
        mock_client.request.assert_not_called()

    def test_unknown_action_returns_1(self):
        from airbyte_api_cli.plugins.state.commands import _handle

        mock_client = MagicMock()
        args = argparse.Namespace(action="unknown")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 1)


# ---------------------------------------------------------------------------
# Plugin registration test
# ---------------------------------------------------------------------------


class TestStatePluginRegistration(unittest.TestCase):
    def setUp(self):
        from airbyte_api_cli.core.registry import Registry
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib

        from airbyte_api_cli.core.registry import Registry
        import airbyte_api_cli.plugins.state
        importlib.reload(airbyte_api_cli.plugins.state)
        plugin = Registry.instance().get_plugin("state")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "state")


if __name__ == "__main__":
    unittest.main()
