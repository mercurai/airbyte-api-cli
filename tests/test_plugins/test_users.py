"""Tests for the users plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_api_cli.plugins.users.api import UsersApi
from airbyte_api_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_client": lambda: mock_client, "format": "json"}


class TestUsersApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = UsersApi(self.client)

    def test_list_returns_api_response(self):
        self.client.request.return_value = {
            "data": [{"userId": "u1", "name": "Alice"}],
        }
        result = self.api.list(organization_id="org1")
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["userId"], "u1")

    def test_list_passes_organization_id_param(self):
        self.client.request.return_value = {"data": []}
        self.api.list(organization_id="org1")
        self.client.request.assert_called_once_with(
            "GET", "users", params={"organizationId": "org1", "limit": 20, "offset": 0}
        )

    def test_list_passes_custom_pagination(self):
        self.client.request.return_value = {"data": []}
        self.api.list(organization_id="org1", limit=5, offset=10)
        self.client.request.assert_called_once_with(
            "GET", "users", params={"organizationId": "org1", "limit": 5, "offset": 10}
        )

    def test_list_empty_data(self):
        self.client.request.return_value = {}
        result = self.api.list(organization_id="org1")
        self.assertEqual(result.data, [])

    def test_list_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api.example.com/users?offset=20",
        }
        result = self.api.list(organization_id="org1")
        self.assertIsNotNone(result.next_url)


class TestUsersCommands(unittest.TestCase):
    def test_list_command_registered(self):
        from airbyte_api_cli.plugins.users.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["users", "list", "--organization-id", "org1"])
        self.assertEqual(args.action, "list")
        self.assertEqual(args.organization_id, "org1")

    def test_list_command_default_pagination(self):
        from airbyte_api_cli.plugins.users.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["users", "list", "--organization-id", "org1"])
        self.assertEqual(args.limit, 20)
        self.assertEqual(args.offset, 0)

    def test_handle_no_action_returns_1(self):
        from airbyte_api_cli.plugins.users.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        from airbyte_api_cli.plugins.users.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"data": [{"userId": "u1"}]}
        args = argparse.Namespace(action="list", organization_id="org1", limit=20, offset=0)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "GET", "users",
            params={"organizationId": "org1", "limit": 20, "offset": 0},
        )


if __name__ == "__main__":
    unittest.main()
