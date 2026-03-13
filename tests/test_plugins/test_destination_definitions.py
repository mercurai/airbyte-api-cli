"""Tests for the destination_definitions plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_api_cli.plugins.destination_definitions.api import DestinationDefinitionsApi
from airbyte_api_cli.plugins.destination_definitions.models import DestinationDefinitionCreate
from airbyte_api_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


class TestDestinationDefinitionCreate(unittest.TestCase):
    def test_to_dict_minimal(self):
        payload = DestinationDefinitionCreate(
            name="Snowflake",
            docker_repository="airbyte/destination-snowflake",
            docker_image_tag="1.0.0",
        )
        d = payload.to_dict()
        self.assertEqual(d["name"], "Snowflake")
        self.assertEqual(d["dockerRepository"], "airbyte/destination-snowflake")
        self.assertEqual(d["dockerImageTag"], "1.0.0")
        self.assertNotIn("documentationUrl", d)

    def test_to_dict_with_documentation_url(self):
        payload = DestinationDefinitionCreate(
            name="Snowflake",
            docker_repository="airbyte/destination-snowflake",
            docker_image_tag="1.0.0",
            documentation_url="https://docs.airbyte.com/snowflake",
        )
        d = payload.to_dict()
        self.assertEqual(d["documentationUrl"], "https://docs.airbyte.com/snowflake")


class TestDestinationDefinitionsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = DestinationDefinitionsApi(self.client)

    def test_list_calls_post(self):
        self.client.request.return_value = {
            "destinationDefinitions": [{"destinationDefinitionId": "dd1", "name": "Snowflake"}],
        }
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data[0]["destinationDefinitionId"], "dd1")
        self.client.request.assert_called_once_with(
            "POST", "destination_definitions/list", body={}
        )

    def test_list_with_workspace(self):
        self.client.request.return_value = {"destinationDefinitions": []}
        self.api.list(workspace_id="ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "destination_definitions/list_for_workspace",
            body={"workspaceId": "ws1"},
        )

    def test_get_sends_post(self):
        self.client.request.return_value = {"destinationDefinitionId": "dd1"}
        result = self.api.get("dd1")
        self.client.request.assert_called_once_with(
            "POST",
            "destination_definitions/get",
            body={"destinationDefinitionId": "dd1"},
        )
        self.assertEqual(result["destinationDefinitionId"], "dd1")

    def test_create_sends_create_custom(self):
        self.client.request.return_value = {"destinationDefinitionId": "dd2"}
        payload = DestinationDefinitionCreate(
            name="BigQuery",
            docker_repository="airbyte/destination-bigquery",
            docker_image_tag="1.5.0",
        )
        result = self.api.create(payload, workspace_id="ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "destination_definitions/create_custom",
            body={
                "workspaceId": "ws1",
                "destinationDefinition": payload.to_dict(),
            },
        )
        self.assertEqual(result["destinationDefinitionId"], "dd2")

    def test_update_sends_post_with_id(self):
        self.client.request.return_value = {"destinationDefinitionId": "dd1"}
        payload = DestinationDefinitionCreate(
            name="BigQuery",
            docker_repository="airbyte/destination-bigquery",
            docker_image_tag="1.6.0",
        )
        self.api.update("dd1", payload)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["destinationDefinitionId"], "dd1")
        self.assertEqual(call_body["name"], "BigQuery")

    def test_delete_sends_post(self):
        self.client.request.return_value = {}
        self.api.delete("dd1")
        self.client.request.assert_called_once_with(
            "POST",
            "destination_definitions/delete",
            body={"destinationDefinitionId": "dd1"},
        )

    def test_list_empty(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])


class TestDestinationDefinitionsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["destination_definitions", "list"])
        self.assertEqual(args.action, "list")

    def test_get_command_requires_id(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["destination_definitions", "get", "--id", "dd1"])
        self.assertEqual(args.definition_id, "dd1")

    def test_handle_no_action_returns_1(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"destinationDefinitions": []}
        args = argparse.Namespace(action="list", workspace_id=None)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST", "destination_definitions/list", body={}
        )

    def test_handle_get_calls_api(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"destinationDefinitionId": "dd1"}
        args = argparse.Namespace(action="get", definition_id="dd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)

    def test_handle_create_calls_api(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"destinationDefinitionId": "dd2"}
        args = argparse.Namespace(
            action="create",
            name="BigQuery",
            docker_repository="airbyte/destination-bigquery",
            docker_image_tag="1.5.0",
            documentation_url="",
            workspace_id="ws1",
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["destinationDefinition"]["name"], "BigQuery")

    def test_handle_delete_calls_api(self):
        from airbyte_api_cli.plugins.destination_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", definition_id="dd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "destination_definitions/delete",
            body={"destinationDefinitionId": "dd1"},
        )


if __name__ == "__main__":
    unittest.main()
