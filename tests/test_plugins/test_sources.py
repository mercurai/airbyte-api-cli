"""Tests for the sources plugin."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.sources.api import SourcesApi
from airbyte_api_cli.plugins.sources.models import Source, SourceCreate


class TestSourceModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "sourceId": "src-1",
            "name": "My Postgres",
            "sourceType": "postgres",
            "workspaceId": "ws-1",
            "configuration": {"host": "localhost"},
            "definitionId": "def-1",
            "createdAt": 1700000000,
        }
        src = Source.from_dict(data)
        self.assertEqual(src.source_id, "src-1")
        self.assertEqual(src.name, "My Postgres")
        self.assertEqual(src.source_type, "postgres")
        self.assertEqual(src.workspace_id, "ws-1")
        self.assertEqual(src.configuration, {"host": "localhost"})
        self.assertEqual(src.definition_id, "def-1")
        self.assertEqual(src.created_at, 1700000000)

    def test_from_dict_minimal(self):
        src = Source.from_dict({})
        self.assertEqual(src.source_id, "")
        self.assertEqual(src.name, "")
        self.assertEqual(src.configuration, {})

    def test_to_dict_roundtrip(self):
        data = {
            "sourceId": "src-2",
            "name": "S3",
            "sourceType": "s3",
            "workspaceId": "ws-2",
            "configuration": {"bucket": "my-bucket"},
            "definitionId": "",
            "createdAt": 0,
        }
        src = Source.from_dict(data)
        self.assertEqual(src.to_dict(), data)

    def test_source_create_to_dict(self):
        sc = SourceCreate(
            name="Postgres",
            workspace_id="ws-1",
            source_type="postgres",
            configuration={"host": "db.example.com"},
        )
        d = sc.to_dict()
        self.assertEqual(d["name"], "Postgres")
        self.assertEqual(d["workspaceId"], "ws-1")
        self.assertEqual(d["sourceType"], "postgres")
        self.assertNotIn("definitionId", d)

    def test_source_create_includes_definition_id_when_set(self):
        sc = SourceCreate(
            name="Postgres",
            workspace_id="ws-1",
            source_type="postgres",
            configuration={},
            definition_id="def-123",
        )
        d = sc.to_dict()
        self.assertEqual(d["definitionId"], "def-123")


class TestSourcesApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_list_builds_correct_params(self):
        self.client.request.return_value = {"data": [], "next": None, "previous": None}
        api = SourcesApi(self.client)
        result = api.list(limit=10, offset=5)
        self.client.request.assert_called_once_with(
            "GET", "sources", params={"limit": 10, "offset": 5}
        )
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data, [])

    def test_list_with_workspace_ids(self):
        self.client.request.return_value = {"data": [{"sourceId": "s1"}]}
        api = SourcesApi(self.client)
        result = api.list(workspace_ids=["ws-1", "ws-2"])
        call_params = self.client.request.call_args[1]["params"]
        self.assertEqual(call_params["workspaceIds"], "ws-1,ws-2")
        self.assertEqual(len(result.data), 1)

    def test_list_returns_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api/sources?offset=20",
            "previous": None,
        }
        api = SourcesApi(self.client)
        result = api.list()
        self.assertEqual(result.next_url, "https://api/sources?offset=20")
        self.assertIsNone(result.previous_url)

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {"sourceId": "src-1", "name": "PG"}
        api = SourcesApi(self.client)
        result = api.get("src-1")
        self.client.request.assert_called_once_with("GET", "sources/src-1")
        self.assertEqual(result["sourceId"], "src-1")

    def test_create_posts_payload(self):
        self.client.request.return_value = {"sourceId": "new-src"}
        api = SourcesApi(self.client)
        sc = SourceCreate(
            name="My Source",
            workspace_id="ws-1",
            source_type="postgres",
            configuration={"host": "localhost"},
        )
        result = api.create(sc)
        self.client.request.assert_called_once_with("POST", "sources", body=sc.to_dict())
        self.assertEqual(result["sourceId"], "new-src")

    def test_update_sends_patch(self):
        self.client.request.return_value = {"sourceId": "src-1", "name": "Updated"}
        api = SourcesApi(self.client)
        result = api.update("src-1", {"name": "Updated"})
        self.client.request.assert_called_once_with(
            "PATCH", "sources/src-1", body={"name": "Updated"}
        )

    def test_replace_sends_put(self):
        self.client.request.return_value = {"sourceId": "src-1"}
        api = SourcesApi(self.client)
        sc = SourceCreate(
            name="Replaced",
            workspace_id="ws-1",
            source_type="postgres",
            configuration={},
        )
        api.replace("src-1", sc)
        self.client.request.assert_called_once_with(
            "PUT", "sources/src-1", body=sc.to_dict()
        )

    def test_delete_sends_delete(self):
        self.client.request.return_value = {}
        api = SourcesApi(self.client)
        api.delete("src-1")
        self.client.request.assert_called_once_with("DELETE", "sources/src-1")

    def test_oauth_posts_to_oauth_endpoint(self):
        self.client.request.return_value = {"redirectUrl": "https://oauth.example.com"}
        api = SourcesApi(self.client)
        payload = {"workspaceId": "ws-1", "sourceType": "github"}
        result = api.oauth(payload)
        self.client.request.assert_called_once_with("POST", "sources/oauth", body=payload)
        self.assertIn("redirectUrl", result)


class TestSourcesPluginRegistration(unittest.TestCase):
    def setUp(self):
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        import airbyte_api_cli.plugins.sources
        importlib.reload(airbyte_api_cli.plugins.sources)
        plugin = Registry.instance().get_plugin("sources")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "sources")


class TestSourcesCommands(unittest.TestCase):
    """Test command handler dispatch logic."""

    def _make_context(self):
        client = MagicMock()
        return {"get_client": lambda: client, "format": "json", "_client": client}

    def test_handle_list(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"data": [{"sourceId": "s1"}]}

        args = MagicMock()
        args.action = "list"
        args.workspace_id = None
        args.limit = 20
        args.offset = 0

        with patch("airbyte_api_cli.plugins.sources.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_get(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"sourceId": "s1"}

        args = MagicMock()
        args.action = "get"
        args.source_id = "s1"

        with patch("airbyte_api_cli.plugins.sources.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_create(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"sourceId": "new"}

        args = MagicMock()
        args.action = "create"
        args.name = "My Source"
        args.workspace_id = "ws-1"
        args.source_type = "postgres"
        args.configuration = '{"host": "localhost"}'
        args.definition_id = ""

        with patch("airbyte_api_cli.plugins.sources.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_update(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"sourceId": "s1"}

        args = MagicMock()
        args.action = "update"
        args.source_id = "s1"
        args.data = '{"name": "New Name"}'

        with patch("airbyte_api_cli.plugins.sources.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_replace(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"sourceId": "s1"}

        args = MagicMock()
        args.action = "replace"
        args.source_id = "s1"
        args.name = "Replaced"
        args.workspace_id = "ws-1"
        args.source_type = "postgres"
        args.configuration = "{}"
        args.definition_id = ""

        with patch("airbyte_api_cli.plugins.sources.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_delete(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {}

        args = MagicMock()
        args.action = "delete"
        args.source_id = "s1"

        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_oauth(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"redirectUrl": "https://oauth.example.com"}

        args = MagicMock()
        args.action = "oauth"
        args.data = '{"workspaceId": "ws-1", "sourceType": "github"}'

        with patch("airbyte_api_cli.plugins.sources.commands.output"):
            result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_handle_unknown_action(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()

        args = MagicMock()
        args.action = "unknown"

        with patch("airbyte_api_cli.plugins.sources.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_list_with_all_flag(self):
        from airbyte_api_cli.plugins.sources.commands import _handle
        ctx = self._make_context()
        # First call returns full page, second returns partial (signals end)
        ctx["_client"].request.side_effect = [
            {"data": [{"sourceId": f"s{i}"} for i in range(3)]},
            {"data": [{"sourceId": "s3"}]},
        ]

        args = MagicMock()
        args.action = "list"
        args.workspace_id = None
        args.limit = 3
        args.offset = 0
        args.fetch_all = True

        with patch("airbyte_api_cli.plugins.sources.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        # Should have received all 4 items combined from both pages
        called_data = mock_out.call_args[0][0]
        self.assertEqual(len(called_data), 4)


if __name__ == "__main__":
    unittest.main()
