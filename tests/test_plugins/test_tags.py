"""Tests for the tags plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.tags.api import TagsApi
from airbyte_api_cli.plugins.tags.models import Tag


class TestTagModel(unittest.TestCase):
    def test_from_dict(self):
        data = {"tagId": "t1", "name": "urgent", "color": "#ff0000", "workspaceId": "ws1"}
        tag = Tag.from_dict(data)
        self.assertEqual(tag.tag_id, "t1")
        self.assertEqual(tag.name, "urgent")
        self.assertEqual(tag.color, "#ff0000")
        self.assertEqual(tag.workspace_id, "ws1")

    def test_from_dict_missing_fields(self):
        tag = Tag.from_dict({})
        self.assertEqual(tag.tag_id, "")
        self.assertEqual(tag.name, "")

    def test_to_dict(self):
        tag = Tag(tag_id="t1", name="urgent", color="#ff0000", workspace_id="ws1")
        d = tag.to_dict()
        self.assertEqual(d["tagId"], "t1")
        self.assertEqual(d["name"], "urgent")
        self.assertEqual(d["color"], "#ff0000")
        self.assertEqual(d["workspaceId"], "ws1")


class TestTagsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = TagsApi(self.client)

    def test_list_returns_api_response(self):
        self.client.request.return_value = {"data": [{"tagId": "t1"}], "next": None}
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.client.request.assert_called_once_with("GET", "tags", params={})

    def test_list_passes_params(self):
        self.client.request.return_value = {"data": []}
        self.api.list(workspaceId="ws1", limit=10)
        self.client.request.assert_called_once_with(
            "GET", "tags", params={"workspaceId": "ws1", "limit": 10}
        )

    def test_get(self):
        self.client.request.return_value = {"tagId": "t1"}
        result = self.api.get("t1")
        self.assertEqual(result["tagId"], "t1")
        self.client.request.assert_called_once_with("GET", "tags/t1")

    def test_create(self):
        self.client.request.return_value = {"tagId": "t2", "name": "new"}
        result = self.api.create({"name": "new"})
        self.assertEqual(result["tagId"], "t2")
        self.client.request.assert_called_once_with("POST", "tags", body={"name": "new"})

    def test_update(self):
        self.client.request.return_value = {"tagId": "t1", "name": "updated"}
        result = self.api.update("t1", {"name": "updated"})
        self.assertEqual(result["name"], "updated")
        self.client.request.assert_called_once_with("PATCH", "tags/t1", body={"name": "updated"})

    def test_delete(self):
        self.client.request.return_value = {}
        self.api.delete("t1")
        self.client.request.assert_called_once_with("DELETE", "tags/t1")


class TestTagsCommands(unittest.TestCase):
    def setUp(self):
        Registry.reset()
        import importlib
        import airbyte_api_cli.plugins.tags as _mod
        importlib.reload(_mod)

    def _run_handler(self, argv):
        import argparse
        from airbyte_api_cli.plugins.tags.commands import register_commands, _handle

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd")
        mock_client = MagicMock()
        context = {"get_client": lambda: mock_client, "format": "json"}
        register_commands(subparsers, context)

        args = parser.parse_args(["tags"] + argv)
        return _handle(args, context), mock_client

    def test_list_command(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"data": [{"tagId": "t1"}]}
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action="list", workspace_id=None, limit=20, offset=0)
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("GET", "tags", params={"limit": 20, "offset": 0})

    def test_get_command(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"tagId": "t1"}
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action="get", tag_id="t1")
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("GET", "tags/t1")

    def test_create_command(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"tagId": "t2"}
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action="create", name="urgent", color=None, workspace_id=None)
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("POST", "tags", body={"name": "urgent"})

    def test_update_command(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {"tagId": "t1", "name": "new-name"}
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action="update", tag_id="t1", name="new-name", color=None)
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with(
            "PATCH", "tags/t1", body={"name": "new-name"}
        )

    def test_delete_command(self):
        mock_client = MagicMock()
        mock_client.request.return_value = {}
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action="delete", tag_id="t1")
        rc = _handle(args, context)
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("DELETE", "tags/t1")

    def test_no_action_returns_error(self):
        mock_client = MagicMock()
        context = {"get_client": lambda: mock_client, "format": "json"}

        import argparse
        from airbyte_api_cli.plugins.tags.commands import _handle

        args = argparse.Namespace(action=None)
        rc = _handle(args, context)
        self.assertEqual(rc, 1)

    def test_plugin_registered(self):
        from airbyte_api_cli.plugins.tags import register
        Registry.reset()
        register()
        self.assertIn("tags", Registry.instance().all_plugins())


if __name__ == "__main__":
    unittest.main()
