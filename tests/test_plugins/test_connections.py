"""Tests for the connections plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.connections.api import ConnectionsApi
from airbyte_api_cli.plugins.connections.models import Connection


class TestConnectionModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "connectionId": "conn_1",
            "name": "My Connection",
            "sourceId": "src_1",
            "destinationId": "dst_1",
            "workspaceId": "ws_1",
            "status": "active",
            "dataResidency": "auto",
            "namespaceDefinition": "source",
            "namespaceFormat": "",
            "prefix": "",
            "nonBreakingSchemaUpdatesBehavior": "ignore",
            "schedule": {"scheduleType": "cron", "cronExpression": "0 0 * * *"},
            "configurations": {"streams": []},
            "createdAt": 1700000000,
        }
        conn = Connection.from_dict(data)
        self.assertEqual(conn.connection_id, "conn_1")
        self.assertEqual(conn.name, "My Connection")
        self.assertEqual(conn.source_id, "src_1")
        self.assertEqual(conn.destination_id, "dst_1")
        self.assertEqual(conn.status, "active")
        self.assertEqual(conn.schedule["scheduleType"], "cron")
        self.assertEqual(conn.created_at, 1700000000)

    def test_from_dict_minimal(self):
        conn = Connection.from_dict({"connectionId": "conn_x", "sourceId": "s", "destinationId": "d"})
        self.assertEqual(conn.connection_id, "conn_x")
        self.assertEqual(conn.name, "")
        self.assertEqual(conn.status, "")

    def test_to_dict_roundtrip(self):
        data = {
            "connectionId": "conn_2",
            "name": "Test",
            "sourceId": "src_2",
            "destinationId": "dst_2",
            "workspaceId": "ws_2",
            "status": "inactive",
            "dataResidency": "auto",
            "namespaceDefinition": "destination",
            "namespaceFormat": "",
            "prefix": "stg_",
            "nonBreakingSchemaUpdatesBehavior": "ignore",
            "schedule": {},
            "configurations": {},
            "createdAt": 0,
        }
        conn = Connection.from_dict(data)
        d = conn.to_dict()
        self.assertEqual(d["connectionId"], "conn_2")
        self.assertEqual(d["prefix"], "stg_")
        self.assertEqual(d["status"], "inactive")


class TestConnectionsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=HttpClient)
        self.api = ConnectionsApi(self.client)

    def test_list_calls_get_connections(self):
        self.client.request.return_value = {"data": [{"connectionId": "c1"}], "next": None}
        result = self.api.list(limit=10, offset=0)
        self.client.request.assert_called_once_with("GET", "connections", params={"limit": 10, "offset": 0})
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)

    def test_list_with_workspace_filter(self):
        self.client.request.return_value = {"data": []}
        self.api.list(workspaceId="ws_1", limit=5)
        self.client.request.assert_called_once_with(
            "GET", "connections", params={"workspaceId": "ws_1", "limit": 5}
        )

    def test_list_returns_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api/connections?offset=20",
            "previous": "https://api/connections?offset=0",
        }
        result = self.api.list()
        self.assertEqual(result.next_url, "https://api/connections?offset=20")
        self.assertEqual(result.previous_url, "https://api/connections?offset=0")

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {"connectionId": "conn_1"}
        result = self.api.get("conn_1")
        self.client.request.assert_called_once_with("GET", "connections/conn_1")
        self.assertEqual(result["connectionId"], "conn_1")

    def test_create_posts_to_connections(self):
        payload = {"sourceId": "src_1", "destinationId": "dst_1", "name": "New"}
        self.client.request.return_value = {"connectionId": "conn_new"}
        result = self.api.create(payload)
        self.client.request.assert_called_once_with("POST", "connections", body=payload)
        self.assertEqual(result["connectionId"], "conn_new")

    def test_update_patches_correct_endpoint(self):
        # When the caller supplies an explicit status, no GET is needed —
        # the PATCH goes straight through with the supplied body.
        self.client.request.return_value = {"connectionId": "conn_1", "status": "inactive"}
        result = self.api.update("conn_1", {"status": "inactive"})
        self.client.request.assert_called_once_with(
            "PATCH", "connections/conn_1", body={"status": "inactive"}
        )
        self.assertEqual(result["status"], "inactive")

    def test_update_preserves_status_when_omitted(self):
        # Regression for mercurai/airbyte-mercurai#7: omitting status from a
        # rename PATCH must not reset the connection to active. The guard
        # GETs the current connection first and merges its status into the
        # PATCH body.
        self.client.request.side_effect = [
            {"connectionId": "conn_1", "name": "old", "status": "inactive"},
            {"connectionId": "conn_1", "name": "new", "status": "inactive"},
        ]
        result = self.api.update("conn_1", {"name": "new"})
        self.assertEqual(self.client.request.call_count, 2)
        self.client.request.assert_any_call("GET", "connections/conn_1")
        self.client.request.assert_any_call(
            "PATCH",
            "connections/conn_1",
            body={"name": "new", "status": "inactive"},
        )
        self.assertEqual(result["status"], "inactive")

    def test_update_explicit_status_overrides_current(self):
        # Explicit status in the body wins — no GET, no merge.
        self.client.request.return_value = {"connectionId": "conn_1", "status": "active"}
        self.api.update("conn_1", {"name": "x", "status": "active"})
        self.client.request.assert_called_once_with(
            "PATCH", "connections/conn_1", body={"name": "x", "status": "active"}
        )

    def test_delete_calls_delete_endpoint(self):
        self.client.request.return_value = {}
        self.api.delete("conn_1")
        self.client.request.assert_called_once_with("DELETE", "connections/conn_1")

    def test_list_empty_data_key(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])
        self.assertIsNone(result.next_url)


class TestConnectionsCommands(unittest.TestCase):
    def _make_context(self, responses: dict | None = None):
        client = MagicMock(spec=HttpClient)
        if responses:
            client.request.side_effect = lambda *a, **kw: responses.get(
                (a[0], a[1]), {}
            )
        else:
            client.request.return_value = {}
        return {"get_client": lambda: client, "_client": client, "format": "json"}

    def test_list_command_dispatches(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"data": []}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(
            action="list",
            workspace_id=None,
            limit=20,
            offset=0,
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_get_command_dispatches(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"connectionId": "c1"}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(action="get", connection_id="c1")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_create_command_dispatches(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"connectionId": "new"}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(
            action="create",
            source_id="src_1",
            destination_id="dst_1",
            name="My Conn",
            status=None,
            namespace_definition=None,
            data_residency=None,
            prefix=None,
            schedule=None,
            streams=None,
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        call_body = ctx["_client"].request.call_args[1]["body"]
        self.assertEqual(call_body["sourceId"], "src_1")
        self.assertEqual(call_body["destinationId"], "dst_1")
        self.assertEqual(call_body["name"], "My Conn")

    def test_create_with_schedule(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"connectionId": "new"}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(
            action="create",
            source_id="src_1",
            destination_id="dst_1",
            name=None,
            status=None,
            namespace_definition=None,
            data_residency=None,
            prefix=None,
            schedule='{"scheduleType":"cron","cronExpression":"0 0 * * *"}',
            streams=None,
        )
        _handle(args, ctx)
        body = ctx["_client"].request.call_args[1]["body"]
        self.assertEqual(body["schedule"]["scheduleType"], "cron")

    def test_update_command_dispatches(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {"connectionId": "c1"}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(
            action="update",
            connection_id="c1",
            data='{"status":"inactive"}',
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_delete_command_dispatches(self):
        ctx = self._make_context()
        ctx["_client"].request.return_value = {}
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        args = argparse.Namespace(action="delete", connection_id="c1")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_unknown_action_returns_error(self):
        import argparse
        from airbyte_api_cli.plugins.connections.commands import _handle

        ctx = self._make_context()
        args = argparse.Namespace(action=None)
        result = _handle(args, ctx)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
