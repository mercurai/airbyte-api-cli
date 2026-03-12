"""Tests for the source_definitions plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_cli.plugins.source_definitions.api import SourceDefinitionsApi
from airbyte_cli.plugins.source_definitions.models import SourceDefinitionCreate
from airbyte_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


class TestSourceDefinitionCreate(unittest.TestCase):
    def test_to_dict_minimal(self):
        payload = SourceDefinitionCreate(
            name="Postgres",
            docker_repository="airbyte/source-postgres",
            docker_image_tag="1.0.0",
        )
        d = payload.to_dict()
        self.assertEqual(d["name"], "Postgres")
        self.assertEqual(d["dockerRepository"], "airbyte/source-postgres")
        self.assertEqual(d["dockerImageTag"], "1.0.0")
        self.assertNotIn("documentationUrl", d)

    def test_to_dict_with_documentation_url(self):
        payload = SourceDefinitionCreate(
            name="Postgres",
            docker_repository="airbyte/source-postgres",
            docker_image_tag="1.0.0",
            documentation_url="https://docs.airbyte.com/postgres",
        )
        d = payload.to_dict()
        self.assertEqual(d["documentationUrl"], "https://docs.airbyte.com/postgres")


class TestSourceDefinitionsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = SourceDefinitionsApi(self.client)

    def test_list_calls_post(self):
        self.client.request.return_value = {
            "sourceDefinitions": [{"sourceDefinitionId": "sd1", "name": "Postgres"}],
        }
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data[0]["sourceDefinitionId"], "sd1")
        self.client.request.assert_called_once_with(
            "POST", "source_definitions/list", body={}
        )

    def test_list_with_workspace(self):
        self.client.request.return_value = {"sourceDefinitions": []}
        self.api.list(workspace_id="ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "source_definitions/list_for_workspace",
            body={"workspaceId": "ws1"},
        )

    def test_get_sends_post(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd1"}
        result = self.api.get("sd1")
        self.client.request.assert_called_once_with(
            "POST",
            "source_definitions/get",
            body={"sourceDefinitionId": "sd1"},
        )
        self.assertEqual(result["sourceDefinitionId"], "sd1")

    def test_create_sends_create_custom(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd2"}
        payload = SourceDefinitionCreate(
            name="MySQL", docker_repository="airbyte/source-mysql", docker_image_tag="2.0.0"
        )
        result = self.api.create(payload, workspace_id="ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "source_definitions/create_custom",
            body={
                "workspaceId": "ws1",
                "sourceDefinition": payload.to_dict(),
            },
        )
        self.assertEqual(result["sourceDefinitionId"], "sd2")

    def test_create_without_workspace(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd2"}
        payload = SourceDefinitionCreate(
            name="MySQL", docker_repository="airbyte/source-mysql", docker_image_tag="2.0.0"
        )
        self.api.create(payload)
        body = self.client.request.call_args[1]["body"]
        self.assertNotIn("workspaceId", body)
        self.assertIn("sourceDefinition", body)

    def test_update_sends_post_with_id(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd1"}
        payload = SourceDefinitionCreate(
            name="MySQL", docker_repository="airbyte/source-mysql", docker_image_tag="2.1.0"
        )
        self.api.update("sd1", payload)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["sourceDefinitionId"], "sd1")
        self.assertEqual(call_body["name"], "MySQL")

    def test_delete_sends_post(self):
        self.client.request.return_value = {}
        self.api.delete("sd1")
        self.client.request.assert_called_once_with(
            "POST",
            "source_definitions/delete",
            body={"sourceDefinitionId": "sd1"},
        )

    def test_list_empty(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])


class TestSourceDefinitionsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        from airbyte_cli.plugins.source_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["source_definitions", "list"])
        self.assertEqual(args.action, "list")

    def test_get_command_requires_id(self):
        from airbyte_cli.plugins.source_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["source_definitions", "get", "--id", "sd1"])
        self.assertEqual(args.definition_id, "sd1")

    def test_handle_no_action_returns_1(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitions": []}
        args = argparse.Namespace(action="list", workspace_id=None)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "source_definitions/list", body={}
        )

    def test_handle_get_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "sd1"}
        args = argparse.Namespace(action="get", definition_id="sd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "source_definitions/get",
            body={"sourceDefinitionId": "sd1"},
        )

    def test_handle_create_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "sd2"}
        args = argparse.Namespace(
            action="create",
            name="MySQL",
            docker_repository="airbyte/source-mysql",
            docker_image_tag="2.0.0",
            documentation_url="",
            workspace_id="ws1",
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["sourceDefinition"]["name"], "MySQL")

    def test_handle_delete_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", definition_id="sd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "source_definitions/delete",
            body={"sourceDefinitionId": "sd1"},
        )


if __name__ == "__main__":
    unittest.main()
