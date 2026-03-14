"""Tests for the definition_specifications plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_api_cli.plugins.definition_specifications.api import DefinitionSpecificationsApi


def _make_response(data: dict) -> dict:
    return data


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


class TestDefinitionSpecificationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = DefinitionSpecificationsApi(self.client)

    def test_get_source_spec_sends_correct_body(self):
        self.client.request.return_value = _make_response({"connectionSpecification": {}})
        result = self.api.get_source_spec("sd1", "ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "source_definition_specifications/get",
            body={"sourceDefinitionId": "sd1", "workspaceId": "ws1"},
        )
        self.assertIn("connectionSpecification", result)

    def test_get_destination_spec_sends_correct_body(self):
        self.client.request.return_value = _make_response({"connectionSpecification": {}})
        result = self.api.get_destination_spec("dd1", "ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "destination_definition_specifications/get",
            body={"destinationDefinitionId": "dd1", "workspaceId": "ws1"},
        )
        self.assertIn("connectionSpecification", result)

    def test_get_source_spec_includes_workspace_id(self):
        self.client.request.return_value = {}
        self.api.get_source_spec("sd1", "ws-abc")
        body = self.client.request.call_args[1]["body"]
        self.assertEqual(body["workspaceId"], "ws-abc")
        self.assertEqual(body["sourceDefinitionId"], "sd1")

    def test_get_destination_spec_includes_workspace_id(self):
        self.client.request.return_value = {}
        self.api.get_destination_spec("dd1", "ws-abc")
        body = self.client.request.call_args[1]["body"]
        self.assertEqual(body["workspaceId"], "ws-abc")
        self.assertEqual(body["destinationDefinitionId"], "dd1")


class TestDefinitionSpecificationsCommands(unittest.TestCase):
    def test_source_command_registered(self):
        from airbyte_api_cli.plugins.definition_specifications.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(
            ["definition_specifications", "source", "--id", "sd1", "--workspace-id", "ws1"]
        )
        self.assertEqual(args.action, "source")
        self.assertEqual(args.definition_id, "sd1")
        self.assertEqual(args.workspace_id, "ws1")

    def test_destination_command_registered(self):
        from airbyte_api_cli.plugins.definition_specifications.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(
            ["definition_specifications", "destination", "--id", "dd1", "--workspace-id", "ws1"]
        )
        self.assertEqual(args.action, "destination")
        self.assertEqual(args.definition_id, "dd1")
        self.assertEqual(args.workspace_id, "ws1")

    def test_handle_no_action_returns_1(self):
        from airbyte_api_cli.plugins.definition_specifications.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_source_calls_api(self):
        from airbyte_api_cli.plugins.definition_specifications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"connectionSpecification": {}}
        args = argparse.Namespace(action="source", definition_id="sd1", workspace_id="ws1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "source_definition_specifications/get",
            body={"sourceDefinitionId": "sd1", "workspaceId": "ws1"},
        )

    def test_handle_destination_calls_api(self):
        from airbyte_api_cli.plugins.definition_specifications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"connectionSpecification": {}}
        args = argparse.Namespace(action="destination", definition_id="dd1", workspace_id="ws1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "destination_definition_specifications/get",
            body={"destinationDefinitionId": "dd1", "workspaceId": "ws1"},
        )


class TestDefinitionSpecificationsRegistration(unittest.TestCase):
    def setUp(self):
        from airbyte_api_cli.core.registry import Registry
        Registry.reset()

    def test_plugin_registers_command(self):
        import importlib
        from airbyte_api_cli.core.registry import Registry
        import airbyte_api_cli.plugins.definition_specifications
        importlib.reload(airbyte_api_cli.plugins.definition_specifications)
        plugin = Registry.instance().get_plugin("definition_specifications")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "definition_specifications")


if __name__ == "__main__":
    unittest.main()
