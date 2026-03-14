"""Tests for the operations plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.operations.api import OperationsApi
from airbyte_api_cli.plugins.operations.commands import _handle


def _make_context():
    mock_client = MagicMock(spec=HttpClient)
    return {"get_config_client": lambda: mock_client, "format": "json", "_client": mock_client}


class TestOperationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=HttpClient)
        self.api = OperationsApi(self.client)

    def test_list_posts_to_operations_list(self):
        self.client.request.return_value = {"operations": [{"operationId": "op-1"}]}
        result = self.api.list("conn-1")
        self.client.request.assert_called_once_with(
            "POST", "operations/list",
            body={"connectionId": "conn-1"},
        )
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)

    def test_list_empty_operations_key(self):
        self.client.request.return_value = {}
        result = self.api.list("conn-1")
        self.assertEqual(result.data, [])

    def test_get_posts_to_operations_get(self):
        self.client.request.return_value = {"operationId": "op-1"}
        result = self.api.get("op-1")
        self.client.request.assert_called_once_with(
            "POST", "operations/get",
            body={"operationId": "op-1"},
        )
        self.assertEqual(result["operationId"], "op-1")

    def test_create_posts_correct_body(self):
        self.client.request.return_value = {"operationId": "op-new"}
        config = {"operatorType": "normalization"}
        result = self.api.create("conn-1", "ws-1", "My Op", config)
        self.client.request.assert_called_once_with(
            "POST", "operations/create",
            body={
                "connectionId": "conn-1",
                "workspaceId": "ws-1",
                "name": "My Op",
                "operatorConfiguration": config,
            },
        )
        self.assertEqual(result["operationId"], "op-new")

    def test_update_posts_correct_body(self):
        self.client.request.return_value = {"operationId": "op-1", "name": "Updated"}
        config = {"operatorType": "dbt"}
        result = self.api.update("op-1", "Updated", config)
        self.client.request.assert_called_once_with(
            "POST", "operations/update",
            body={
                "operationId": "op-1",
                "name": "Updated",
                "operatorConfiguration": config,
            },
        )
        self.assertEqual(result["name"], "Updated")

    def test_delete_posts_to_operations_delete(self):
        self.client.request.return_value = {}
        self.api.delete("op-1")
        self.client.request.assert_called_once_with(
            "POST", "operations/delete",
            body={"operationId": "op-1"},
        )

    def test_check_posts_operator_configuration(self):
        self.client.request.return_value = {"status": "succeeded"}
        config = {"operatorType": "normalization"}
        result = self.api.check(config)
        self.client.request.assert_called_once_with(
            "POST", "operations/check",
            body={"operatorConfiguration": config},
        )
        self.assertEqual(result["status"], "succeeded")


class TestOperationsCommands(unittest.TestCase):
    def test_list_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {"operations": []}
        args = argparse.Namespace(action="list", connection_id="conn-1")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        ctx["_client"].request.assert_called_once_with(
            "POST", "operations/list",
            body={"connectionId": "conn-1"},
        )

    def test_get_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {"operationId": "op-1"}
        args = argparse.Namespace(action="get", operation_id="op-1")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        ctx["_client"].request.assert_called_once_with(
            "POST", "operations/get",
            body={"operationId": "op-1"},
        )

    def test_create_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {"operationId": "op-new"}
        args = argparse.Namespace(
            action="create",
            connection_id="conn-1",
            workspace_id="ws-1",
            name="My Op",
            config='{"operatorType": "normalization"}',
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        body = ctx["_client"].request.call_args[1]["body"]
        self.assertEqual(body["connectionId"], "conn-1")
        self.assertEqual(body["workspaceId"], "ws-1")
        self.assertEqual(body["name"], "My Op")
        self.assertEqual(body["operatorConfiguration"]["operatorType"], "normalization")

    def test_update_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {"operationId": "op-1"}
        args = argparse.Namespace(
            action="update",
            operation_id="op-1",
            name="New Name",
            config='{"operatorType": "dbt"}',
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        body = ctx["_client"].request.call_args[1]["body"]
        self.assertEqual(body["operationId"], "op-1")
        self.assertEqual(body["name"], "New Name")
        self.assertEqual(body["operatorConfiguration"]["operatorType"], "dbt")

    def test_delete_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {}
        args = argparse.Namespace(action="delete", operation_id="op-1")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        ctx["_client"].request.assert_called_once_with(
            "POST", "operations/delete",
            body={"operationId": "op-1"},
        )

    def test_check_command_dispatches(self):
        ctx = _make_context()
        ctx["_client"].request.return_value = {"status": "succeeded"}
        args = argparse.Namespace(
            action="check",
            config='{"operatorType": "normalization"}',
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        body = ctx["_client"].request.call_args[1]["body"]
        self.assertEqual(body["operatorConfiguration"]["operatorType"], "normalization")

    def test_unknown_action_returns_error(self):
        ctx = _make_context()
        args = argparse.Namespace(action=None)
        result = _handle(args, ctx)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
