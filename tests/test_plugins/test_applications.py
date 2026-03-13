"""Tests for the applications plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.applications.api import ApplicationsApi
from airbyte_api_cli.plugins.applications.models import Application


class TestApplicationModel(unittest.TestCase):
    def test_from_dict(self):
        data = {
            "applicationId": "app1",
            "name": "my-app",
            "clientId": "cid1",
            "clientSecret": "sec1",
            "createdAt": 1000,
        }
        app = Application.from_dict(data)
        self.assertEqual(app.application_id, "app1")
        self.assertEqual(app.name, "my-app")
        self.assertEqual(app.client_id, "cid1")
        self.assertEqual(app.client_secret, "sec1")
        self.assertEqual(app.created_at, 1000)

    def test_from_dict_missing_fields(self):
        app = Application.from_dict({})
        self.assertEqual(app.application_id, "")
        self.assertEqual(app.created_at, 0)

    def test_to_dict(self):
        app = Application(
            application_id="app1",
            name="my-app",
            client_id="cid1",
            client_secret="sec1",
            created_at=1000,
        )
        d = app.to_dict()
        self.assertEqual(d["applicationId"], "app1")
        self.assertEqual(d["clientId"], "cid1")
        self.assertEqual(d["clientSecret"], "sec1")


class TestApplicationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = ApplicationsApi(self.client)

    def test_list_returns_api_response(self):
        self.client.request.return_value = {"data": [{"applicationId": "app1"}]}
        result = self.api.list()
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)
        self.client.request.assert_called_once_with("GET", "applications", params={})

    def test_get(self):
        self.client.request.return_value = {"applicationId": "app1"}
        result = self.api.get("app1")
        self.assertEqual(result["applicationId"], "app1")
        self.client.request.assert_called_once_with("GET", "applications/app1")

    def test_create(self):
        self.client.request.return_value = {"applicationId": "app2", "name": "new-app"}
        result = self.api.create({"name": "new-app"})
        self.assertEqual(result["applicationId"], "app2")
        self.client.request.assert_called_once_with(
            "POST", "applications", body={"name": "new-app"}
        )

    def test_delete(self):
        self.client.request.return_value = {}
        self.api.delete("app1")
        self.client.request.assert_called_once_with("DELETE", "applications/app1")

    def test_token(self):
        self.client.request.return_value = {"access_token": "tok123"}
        result = self.api.token("app1")
        self.assertEqual(result["access_token"], "tok123")
        self.client.request.assert_called_once_with("POST", "applications/app1/token")


class TestApplicationsCommands(unittest.TestCase):
    def setUp(self):
        Registry.reset()
        import importlib
        import airbyte_api_cli.plugins.applications as _mod
        importlib.reload(_mod)

    def _make_context(self, mock_client):
        return {"get_client": lambda: mock_client, "format": "json"}

    def test_list_command(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"data": []}
        args = argparse.Namespace(action="list", limit=20, offset=0)
        rc = _handle(args, self._make_context(mock_client))
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with(
            "GET", "applications", params={"limit": 20, "offset": 0}
        )

    def test_get_command(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"applicationId": "app1"}
        args = argparse.Namespace(action="get", application_id="app1")
        rc = _handle(args, self._make_context(mock_client))
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("GET", "applications/app1")

    def test_create_command(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"applicationId": "app2"}
        args = argparse.Namespace(action="create", name="my-app")
        rc = _handle(args, self._make_context(mock_client))
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with(
            "POST", "applications", body={"name": "my-app"}
        )

    def test_delete_command(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", application_id="app1")
        rc = _handle(args, self._make_context(mock_client))
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("DELETE", "applications/app1")

    def test_token_command(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"access_token": "tok"}
        args = argparse.Namespace(action="token", application_id="app1")
        rc = _handle(args, self._make_context(mock_client))
        self.assertEqual(rc, 0)
        mock_client.request.assert_called_once_with("POST", "applications/app1/token")

    def test_no_action_returns_error(self):
        import argparse
        from airbyte_api_cli.plugins.applications.commands import _handle

        args = argparse.Namespace(action=None)
        rc = _handle(args, self._make_context(MagicMock()))
        self.assertEqual(rc, 1)

    def test_plugin_registered(self):
        from airbyte_api_cli.plugins.applications import register
        Registry.reset()
        register()
        self.assertIn("applications", Registry.instance().all_plugins())


if __name__ == "__main__":
    unittest.main()
