"""Tests for the declarative_source_definitions plugin."""

import unittest
from unittest.mock import MagicMock

from airbyte_cli.plugins.declarative_source_definitions.api import DeclarativeSourceDefinitionsApi
from airbyte_cli.plugins.declarative_source_definitions.models import DeclarativeSourceDefinitionCreate
from airbyte_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


class TestDeclarativeSourceDefinitionCreate(unittest.TestCase):
    def test_to_dict_full(self):
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id="ws1",
            source_definition_id="sd1",
            manifest={"version": "0.1.0"},
            spec={"connectionSpecification": {}},
            description="A test connector",
            version=1,
        )
        d = payload.to_dict()
        self.assertEqual(d["workspaceId"], "ws1")
        self.assertEqual(d["sourceDefinitionId"], "sd1")
        self.assertTrue(d["setAsActiveManifest"])
        self.assertEqual(d["declarativeManifest"]["manifest"], {"version": "0.1.0"})
        self.assertEqual(d["declarativeManifest"]["spec"], {"connectionSpecification": {}})
        self.assertEqual(d["declarativeManifest"]["description"], "A test connector")
        self.assertEqual(d["declarativeManifest"]["version"], 1)

    def test_to_dict_no_description(self):
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id="ws1",
            source_definition_id="sd1",
        )
        d = payload.to_dict()
        self.assertNotIn("description", d["declarativeManifest"])

    def test_defaults(self):
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id="ws1", source_definition_id="sd1"
        )
        self.assertEqual(payload.manifest, {})
        self.assertEqual(payload.spec, {})
        self.assertEqual(payload.version, 0)
        self.assertTrue(payload.set_as_active)


class TestDeclarativeSourceDefinitionsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = DeclarativeSourceDefinitionsApi(self.client)

    def test_list_manifests(self):
        self.client.request.return_value = {
            "manifestVersions": [{"version": 0}],
        }
        result = self.api.list_manifests("ws1", "sd1")
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.client.request.assert_called_once_with(
            "POST",
            "declarative_source_definitions/list_manifests",
            body={"workspaceId": "ws1", "sourceDefinitionId": "sd1"},
        )

    def test_create_manifest(self):
        self.client.request.return_value = {}
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id="ws1",
            source_definition_id="sd1",
            manifest={"version": "0.1.0"},
            spec={},
        )
        self.api.create_manifest(payload)
        self.client.request.assert_called_once_with(
            "POST",
            "declarative_source_definitions/create_manifest",
            body=payload.to_dict(),
        )

    def test_update_manifest(self):
        self.client.request.return_value = {}
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id="ws1",
            source_definition_id="sd1",
            manifest={"version": "0.2.0"},
            spec={},
            version=1,
        )
        self.api.update_manifest(payload)
        self.client.request.assert_called_once_with(
            "POST",
            "declarative_source_definitions/update_active_manifest",
            body=payload.to_dict(),
        )

    def test_list_manifests_empty(self):
        self.client.request.return_value = {}
        result = self.api.list_manifests("ws1", "sd1")
        self.assertEqual(result.data, [])


class TestDeclarativeSourceDefinitionsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "declarative_source_definitions", "list",
            "--workspace-id", "ws1",
            "--source-definition-id", "sd1",
        ])
        self.assertEqual(args.action, "list")
        self.assertEqual(args.workspace_id, "ws1")
        self.assertEqual(args.source_definition_id, "sd1")

    def test_handle_no_action_returns_1(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"manifestVersions": []}
        args = argparse.Namespace(
            action="list", workspace_id="ws1", source_definition_id="sd1"
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "declarative_source_definitions/list_manifests",
            body={"workspaceId": "ws1", "sourceDefinitionId": "sd1"},
        )

    def test_handle_create_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(
            action="create",
            workspace_id="ws1",
            source_definition_id="sd1",
            manifest='{"version": "0.1.0"}',
            spec="{}",
            description="test",
            version=0,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["sourceDefinitionId"], "sd1")
        self.assertTrue(call_body["setAsActiveManifest"])

    def test_handle_update_calls_api(self):
        import argparse
        from airbyte_cli.plugins.declarative_source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(
            action="update",
            workspace_id="ws1",
            source_definition_id="sd1",
            manifest='{"version": "0.2.0"}',
            spec="{}",
            description="",
            version=1,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once()
        self.assertIn("update_active_manifest", mock_client.request.call_args[0][1])


if __name__ == "__main__":
    unittest.main()
