"""Tests for the destinations plugin."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from airbyte_cli.core.registry import Registry
from airbyte_cli.models.common import ApiResponse
from airbyte_cli.plugins.destinations.api import DestinationsApi
from airbyte_cli.plugins.destinations.models import Destination, DestinationCreate


class TestDestinationModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "destinationId": "dst-1",
            "name": "My BigQuery",
            "destinationType": "bigquery",
            "workspaceId": "ws-1",
            "configuration": {"project_id": "my-project"},
            "definitionId": "def-1",
            "createdAt": 1700000000,
        }
        dst = Destination.from_dict(data)
        self.assertEqual(dst.destination_id, "dst-1")
        self.assertEqual(dst.name, "My BigQuery")
        self.assertEqual(dst.destination_type, "bigquery")
        self.assertEqual(dst.workspace_id, "ws-1")
        self.assertEqual(dst.configuration, {"project_id": "my-project"})
        self.assertEqual(dst.definition_id, "def-1")
        self.assertEqual(dst.created_at, 1700000000)

    def test_from_dict_minimal(self):
        dst = Destination.from_dict({})
        self.assertEqual(dst.destination_id, "")
        self.assertEqual(dst.name, "")
        self.assertEqual(dst.configuration, {})

    def test_to_dict_roundtrip(self):
        data = {
            "destinationId": "dst-2",
            "name": "Snowflake",
            "destinationType": "snowflake",
            "workspaceId": "ws-2",
            "configuration": {"account": "xy12345"},
            "definitionId": "",
            "createdAt": 0,
        }
        dst = Destination.from_dict(data)
        self.assertEqual(dst.to_dict(), data)

    def test_destination_create_to_dict(self):
        dc = DestinationCreate(
            name="BigQuery",
            workspace_id="ws-1",
            destination_type="bigquery",
            configuration={"project_id": "proj"},
        )
        d = dc.to_dict()
        self.assertEqual(d["name"], "BigQuery")
        self.assertEqual(d["workspaceId"], "ws-1")
        self.assertEqual(d["destinationType"], "bigquery")
        self.assertNotIn("definitionId", d)

    def test_destination_create_includes_definition_id_when_set(self):
        dc = DestinationCreate(
            name="BigQuery",
            workspace_id="ws-1",
            destination_type="bigquery",
            configuration={},
            definition_id="def-456",
        )
        d = dc.to_dict()
        self.assertEqual(d["definitionId"], "def-456")


class TestDestinationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_list_builds_correct_params(self):
        self.client.request.return_value = {"data": [], "next": None, "previous": None}
        api = DestinationsApi(self.client)
        result = api.list(limit=10, offset=5)
        self.client.request.assert_called_once_with(
            "GET", "destinations", params={"limit": 10, "offset": 5}
        )
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data, [])

    def test_list_with_workspace_ids(self):
        self.client.request.return_value = {"data": [{"destinationId": "d1"}]}
        api = DestinationsApi(self.client)
        result = api.list(workspace_ids=["ws-1", "ws-2"])
        call_params = self.client.request.call_args[1]["params"]
        self.assertEqual(call_params["workspaceIds"], "ws-1,ws-2")
        self.assertEqual(len(result.data), 1)

    def test_list_returns_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api/destinations?offset=20",
            "previous": None,
        }
        api = DestinationsApi(self.client)
        result = api.list()
        self.assertEqual(result.next_url, "https://api/destinations?offset=20")
        self.assertIsNone(result.previous_url)

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {"destinationId": "dst-1", "name": "BQ"}
        api = DestinationsApi(self.client)
        result = api.get("dst-1")
        self.client.request.assert_called_once_with("GET", "destinations/dst-1")
        self.assertEqual(result["destinationId"], "dst-1")

    def test_create_posts_payload(self):
        self.client.request.return_value = {"destinationId": "new-dst"}
        api = DestinationsApi(self.client)
        dc = DestinationCreate(
            name="My Dest",
            workspace_id="ws-1",
            destination_type="bigquery",
            configuration={"project_id": "proj"},
        )
        result = api.create(dc)
        self.client.request.assert_called_once_with("POST", "destinations", body=dc.to_dict())
        self.assertEqual(result["destinationId"], "new-dst")

    def test_update_sends_patch(self):
        self.client.request.return_value = {"destinationId": "dst-1", "name": "Updated"}
        api = DestinationsApi(self.client)
        result = api.update("dst-1", {"name": "Updated"})
        self.client.request.assert_called_once_with(
            "PATCH", "destinations/dst-1", body={"name": "Updated"}
        )

    def test_replace_sends_put(self):
        self.client.request.return_value = {"destinationId": "dst-1"}
        api = DestinationsApi(self.client)
        dc = DestinationCreate(
            name="Replaced",
            workspace_id="ws-1",
            destination_type="bigquery",
            configuration={},
        )
        api.replace("dst-1", dc)
        self.client.request.assert_called_once_with(
            "PUT", "destinations/dst-1", body=dc.to_dict()
        )

    def test_delete_sends_delete(self):
        self.client.request.return_value = {}
        api = DestinationsApi(self.client)
        api.delete("dst-1")
        self.client.request.assert_called_once_with("DELETE", "destinations/dst-1")

    def test_no_oauth_method(self):
        api = DestinationsApi(self.client)
        self.assertFalse(hasattr(api, "oauth"))


class TestDestinationsPluginRegistration(unittest.TestCase):
    def setUp(self):
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        import airbyte_cli.plugins.destinations
        importlib.reload(airbyte_cli.plugins.destinations)
        plugin = Registry.instance().get_plugin("destinations")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "destinations")


class TestDestinationsCommands(unittest.TestCase):
    """Test command handler dispatch logic."""

    def _make_context(self):
        client = MagicMock()
        return {"get_client": lambda: client, "format": "json", "_client": client}

    def test_handle_list(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"data": [{"destinationId": "d1"}]}

        args = MagicMock()
        args.action = "list"
        args.workspace_id = None
        args.limit = 20
        args.offset = 0

        with patch("airbyte_cli.plugins.destinations.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_get(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"destinationId": "d1"}

        args = MagicMock()
        args.action = "get"
        args.destination_id = "d1"

        with patch("airbyte_cli.plugins.destinations.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_create(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"destinationId": "new"}

        args = MagicMock()
        args.action = "create"
        args.name = "My Dest"
        args.workspace_id = "ws-1"
        args.destination_type = "bigquery"
        args.configuration = '{"project_id": "proj"}'
        args.definition_id = ""

        with patch("airbyte_cli.plugins.destinations.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_update(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"destinationId": "d1"}

        args = MagicMock()
        args.action = "update"
        args.destination_id = "d1"
        args.data = '{"name": "New Name"}'

        with patch("airbyte_cli.plugins.destinations.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_replace(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"destinationId": "d1"}

        args = MagicMock()
        args.action = "replace"
        args.destination_id = "d1"
        args.name = "Replaced"
        args.workspace_id = "ws-1"
        args.destination_type = "bigquery"
        args.configuration = "{}"
        args.definition_id = ""

        with patch("airbyte_cli.plugins.destinations.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_delete(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {}

        args = MagicMock()
        args.action = "delete"
        args.destination_id = "d1"

        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_unknown_action(self):
        from airbyte_cli.plugins.destinations.commands import _handle
        ctx = self._make_context()

        args = MagicMock()
        args.action = "unknown"

        with patch("airbyte_cli.plugins.destinations.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()


if __name__ == "__main__":
    unittest.main()
