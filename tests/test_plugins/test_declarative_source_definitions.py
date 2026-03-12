"""Tests for the declarative_source_definitions plugin."""

import unittest
from unittest.mock import MagicMock

from airbyte_cli.plugins.declarative_source_definitions.api import DeclarativeSourceDefinitionsApi
from airbyte_cli.plugins.declarative_source_definitions.models import DeclarativeSourceDefinitionCreate
from airbyte_cli.models.common import ApiResponse


class TestDeclarativeSourceDefinitionCreate(unittest.TestCase):
    def test_to_dict_minimal(self):
        payload = DeclarativeSourceDefinitionCreate(
            name="MyConnector",
            workspace_id="ws1",
            manifest={"version": "0.1.0"},
        )
        d = payload.to_dict()
        self.assertEqual(d["name"], "MyConnector")
        self.assertEqual(d["workspaceId"], "ws1")
        self.assertIn("declarativeManifest", d)
        self.assertEqual(d["declarativeManifest"]["manifest"], {"version": "0.1.0"})

    def test_to_dict_with_description(self):
        payload = DeclarativeSourceDefinitionCreate(
            name="MyConnector",
            workspace_id="ws1",
            manifest={"version": "0.1.0"},
            description="A test connector",
        )
        d = payload.to_dict()
        self.assertEqual(d["declarativeManifest"]["description"], "A test connector")

    def test_to_dict_no_description_when_empty(self):
        payload = DeclarativeSourceDefinitionCreate(
            name="MyConnector",
            workspace_id="ws1",
        )
        d = payload.to_dict()
        self.assertNotIn("description", d["declarativeManifest"])

    def test_default_manifest_is_empty_dict(self):
        payload = DeclarativeSourceDefinitionCreate(name="X", workspace_id="ws1")
        self.assertEqual(payload.manifest, {})


class TestDeclarativeSourceDefinitionsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = DeclarativeSourceDefinitionsApi(self.client)

    def test_list_returns_api_response(self):
        self.client.request.return_value = {
            "data": [{"sourceDefinitionId": "dsd1", "name": "MyConnector"}],
        }
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data[0]["sourceDefinitionId"], "dsd1")

    def test_list_passes_pagination_params(self):
        self.client.request.return_value = {"data": []}
        self.api.list(limit=10, offset=5)
        self.client.request.assert_called_once_with(
            "GET",
            "declarative_source_definitions",
            params={"limit": 10, "offset": 5},
        )

    def test_get_sends_correct_request(self):
        self.client.request.return_value = {"sourceDefinitionId": "dsd1"}
        result = self.api.get("dsd1")
        self.client.request.assert_called_once_with(
            "GET", "declarative_source_definitions/dsd1"
        )
        self.assertEqual(result["sourceDefinitionId"], "dsd1")

    def test_create_sends_post(self):
        self.client.request.return_value = {"sourceDefinitionId": "dsd2"}
        payload = DeclarativeSourceDefinitionCreate(
            name="MyConnector", workspace_id="ws1", manifest={"version": "0.1.0"}
        )
        result = self.api.create(payload)
        self.client.request.assert_called_once_with(
            "POST", "declarative_source_definitions", body=payload.to_dict()
        )
        self.assertEqual(result["sourceDefinitionId"], "dsd2")

    def test_update_sends_put(self):
        self.client.request.return_value = {"sourceDefinitionId": "dsd1"}
        payload = DeclarativeSourceDefinitionCreate(
            name="MyConnector", workspace_id="ws1", manifest={"version": "0.2.0"}
        )
        self.api.update("dsd1", payload)
        self.client.request.assert_called_once_with(
            "PUT", "declarative_source_definitions/dsd1", body=payload.to_dict()
        )

    def test_delete_sends_delete(self):
        self.client.request.return_value = {}
        self.api.delete("dsd1")
        self.client.request.assert_called_once_with(
            "DELETE", "declarative_source_definitions/dsd1"
        )

    def test_list_empty_data(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])


class TestDeclarativeSourceDefinitionsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["declarative_source_definitions", "list"])
        self.assertEqual(args.action, "list")

    def test_create_command_requires_workspace_id(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "declarative_source_definitions", "create",
            "--name", "X", "--workspace-id", "ws1", "--manifest", "{}",
        ])
        self.assertEqual(args.workspace_id, "ws1")

    def test_handle_no_action_returns_1(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, {"get_client": lambda: MagicMock(), "format": "json"})
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"data": []}
        args = argparse.Namespace(action="list", limit=20, offset=0)
        context = {"get_client": lambda: mock_client, "format": "json"}
        result = _handle(args, context)
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "GET", "declarative_source_definitions", params={"limit": 20, "offset": 0}
        )

    def test_handle_create_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "dsd2"}
        args = argparse.Namespace(
            action="create",
            name="X",
            workspace_id="ws1",
            manifest='{"version": "0.1.0"}',
            description="",
        )
        context = {"get_client": lambda: mock_client, "format": "json"}
        result = _handle(args, context)
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once()

    def test_handle_update_uses_put(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(
            action="update",
            definition_id="dsd1",
            name="X",
            workspace_id="ws1",
            manifest='{"version": "0.2.0"}',
            description="",
        )
        context = {"get_client": lambda: mock_client, "format": "json"}
        result = _handle(args, context)
        self.assertEqual(result, 0)
        call_args = mock_client.request.call_args
        self.assertEqual(call_args[0][0], "PUT")

    def test_handle_delete_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", definition_id="dsd1")
        context = {"get_client": lambda: mock_client, "format": "json"}
        result = _handle(args, context)
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "DELETE", "declarative_source_definitions/dsd1"
        )


if __name__ == "__main__":
    unittest.main()
