"""Tests for the source_definitions plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_cli.plugins.source_definitions.api import SourceDefinitionsApi
from airbyte_cli.plugins.source_definitions.models import SourceDefinitionCreate
from airbyte_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_client": lambda: mock_client, "format": "json"}


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

    def test_list_returns_api_response(self):
        self.client.request.return_value = {
            "data": [{"sourceDefinitionId": "sd1", "name": "Postgres"}],
        }
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data[0]["sourceDefinitionId"], "sd1")

    def test_list_passes_pagination_params(self):
        self.client.request.return_value = {"data": []}
        self.api.list(limit=10, offset=5)
        self.client.request.assert_called_once_with(
            "GET", "source_definitions", params={"limit": 10, "offset": 5}
        )

    def test_get_sends_correct_request(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd1"}
        result = self.api.get("sd1")
        self.client.request.assert_called_once_with("GET", "source_definitions/sd1")
        self.assertEqual(result["sourceDefinitionId"], "sd1")

    def test_create_sends_post(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd2"}
        payload = SourceDefinitionCreate(
            name="MySQL", docker_repository="airbyte/source-mysql", docker_image_tag="2.0.0"
        )
        result = self.api.create(payload)
        self.client.request.assert_called_once_with(
            "POST", "source_definitions", body=payload.to_dict()
        )
        self.assertEqual(result["sourceDefinitionId"], "sd2")

    def test_update_sends_put(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd1"}
        payload = SourceDefinitionCreate(
            name="MySQL", docker_repository="airbyte/source-mysql", docker_image_tag="2.1.0"
        )
        self.api.update("sd1", payload)
        self.client.request.assert_called_once_with(
            "PUT", "source_definitions/sd1", body=payload.to_dict()
        )

    def test_delete_sends_delete(self):
        self.client.request.return_value = {}
        self.api.delete("sd1")
        self.client.request.assert_called_once_with("DELETE", "source_definitions/sd1")

    def test_list_empty_data(self):
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
        mock_client.request.return_value = {"data": []}
        args = argparse.Namespace(action="list", limit=20, offset=0)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "GET", "source_definitions", params={"limit": 20, "offset": 0}
        )

    def test_handle_get_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "sd1"}
        args = argparse.Namespace(action="get", definition_id="sd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with("GET", "source_definitions/sd1")

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
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "source_definitions",
            body={
                "name": "MySQL",
                "dockerRepository": "airbyte/source-mysql",
                "dockerImageTag": "2.0.0",
            },
        )

    def test_handle_update_uses_put(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "sd1"}
        args = argparse.Namespace(
            action="update",
            definition_id="sd1",
            name="MySQL",
            docker_repository="airbyte/source-mysql",
            docker_image_tag="2.1.0",
            documentation_url="",
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "PUT",
            "source_definitions/sd1",
            body={
                "name": "MySQL",
                "dockerRepository": "airbyte/source-mysql",
                "dockerImageTag": "2.1.0",
            },
        )

    def test_handle_delete_calls_api(self):
        from airbyte_cli.plugins.source_definitions.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", definition_id="sd1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with("DELETE", "source_definitions/sd1")


if __name__ == "__main__":
    unittest.main()
