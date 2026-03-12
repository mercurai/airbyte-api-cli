"""Tests for the organizations plugin."""

import argparse
import unittest
from unittest.mock import MagicMock

from airbyte_cli.plugins.organizations.api import OrganizationsApi
from airbyte_cli.models.common import ApiResponse


def _ctx(mock_client):
    return {"get_client": lambda: mock_client, "format": "json"}


class TestOrganizationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = OrganizationsApi(self.client)

    def test_list_returns_api_response(self):
        self.client.request.return_value = {
            "data": [{"organizationId": "org1", "name": "Acme"}],
            "next": None,
        }
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["organizationId"], "org1")

    def test_list_passes_pagination_params(self):
        self.client.request.return_value = {"data": []}
        self.api.list(limit=10, offset=5)
        self.client.request.assert_called_once_with(
            "GET", "organizations", params={"limit": 10, "offset": 5}
        )

    def test_list_empty_data(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])
        self.assertIsNone(result.next_url)

    def test_list_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api.example.com/organizations?offset=20",
            "previous": "https://api.example.com/organizations?offset=0",
        }
        result = self.api.list()
        self.assertIsNotNone(result.next_url)
        self.assertIsNotNone(result.previous_url)

    def test_update_oauth_credentials_sends_put(self):
        self.client.request.return_value = {"status": "ok"}
        data = {"clientId": "id1", "clientSecret": "secret1"}
        result = self.api.update_oauth_credentials("org1", data)
        self.client.request.assert_called_once_with(
            "PUT", "organizations/org1/oauthCredentials", body=data
        )
        self.assertEqual(result["status"], "ok")

    def test_update_oauth_credentials_returns_response(self):
        expected = {"organizationId": "org1", "oauthStatus": "configured"}
        self.client.request.return_value = expected
        result = self.api.update_oauth_credentials("org1", {})
        self.assertEqual(result, expected)


class TestOrganizationsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        from airbyte_cli.plugins.organizations.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["organizations", "list"])
        self.assertEqual(args.action, "list")

    def test_list_command_default_pagination(self):
        from airbyte_cli.plugins.organizations.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["organizations", "list"])
        self.assertEqual(args.limit, 20)
        self.assertEqual(args.offset, 0)

    def test_oauth_command_requires_id_and_data(self):
        from airbyte_cli.plugins.organizations.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(
            ["organizations", "oauth", "--id", "org1", "--data", '{"clientId": "c1"}']
        )
        self.assertEqual(args.organization_id, "org1")

    def test_handle_no_action_returns_1(self):
        from airbyte_cli.plugins.organizations.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        from airbyte_cli.plugins.organizations.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"data": []}
        args = argparse.Namespace(action="list", limit=20, offset=0)
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "GET", "organizations", params={"limit": 20, "offset": 0}
        )

    def test_handle_oauth_calls_api(self):
        from airbyte_cli.plugins.organizations.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"status": "ok"}
        args = argparse.Namespace(
            action="oauth", organization_id="org1", data='{"clientId": "c1"}'
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "PUT", "organizations/org1/oauthCredentials", body={"clientId": "c1"}
        )


if __name__ == "__main__":
    unittest.main()
