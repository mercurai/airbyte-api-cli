"""Tests for the workspaces plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.plugins.workspaces import api
from airbyte_api_cli.plugins.workspaces.commands import register_commands, _handle
from airbyte_api_cli.plugins.workspaces.models import Workspace, OAuthCredentials


def _make_client(return_value=None):
    client = MagicMock()
    client.request.return_value = return_value or {}
    return client


def _make_context(client=None):
    c = client or _make_client()
    return {"get_client": lambda: c, "format": "json"}


class TestWorkspaceModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "workspaceId": "ws1",
            "name": "My WS",
            "dataResidency": "US",
            "notifications": [{"type": "email"}],
        }
        ws = Workspace.from_dict(data)
        self.assertEqual(ws.workspaceId, "ws1")
        self.assertEqual(ws.name, "My WS")
        self.assertEqual(ws.dataResidency, "US")
        self.assertEqual(ws.notifications, [{"type": "email"}])

    def test_from_dict_minimal(self):
        data = {"workspaceId": "ws2", "name": "Minimal"}
        ws = Workspace.from_dict(data)
        self.assertIsNone(ws.dataResidency)
        self.assertEqual(ws.notifications, [])

    def test_to_dict_roundtrip(self):
        data = {"workspaceId": "ws3", "name": "RoundTrip", "dataResidency": "EU", "notifications": []}
        ws = Workspace.from_dict(data)
        result = ws.to_dict()
        self.assertEqual(result["workspaceId"], "ws3")
        self.assertEqual(result["dataResidency"], "EU")

    def test_oauth_credentials_to_dict(self):
        creds = OAuthCredentials(actorType="source", name="my-cred", configuration={"key": "val"})
        d = creds.to_dict()
        self.assertEqual(d["actorType"], "source")
        self.assertEqual(d["name"], "my-cred")
        self.assertEqual(d["configuration"]["key"], "val")


class TestWorkspacesApi(unittest.TestCase):
    def test_list_workspaces(self):
        client = _make_client({"data": [{"workspaceId": "ws1", "name": "A"}]})
        result = api.list_workspaces(client)
        client.request.assert_called_once_with("GET", "/workspaces")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["workspaceId"], "ws1")

    def test_list_workspaces_empty(self):
        client = _make_client({})
        result = api.list_workspaces(client)
        self.assertEqual(result, [])

    def test_get_workspace(self):
        client = _make_client({"workspaceId": "ws1", "name": "A"})
        result = api.get_workspace(client, "ws1")
        client.request.assert_called_once_with("GET", "/workspaces/ws1")
        self.assertEqual(result["workspaceId"], "ws1")

    def test_create_workspace_minimal(self):
        client = _make_client({"workspaceId": "ws_new", "name": "New"})
        api.create_workspace(client, name="New")
        client.request.assert_called_once_with("POST", "/workspaces", body={"name": "New"})

    def test_create_workspace_full(self):
        client = _make_client({"workspaceId": "ws_new"})
        api.create_workspace(client, name="Full", organization_id="org1", data_residency="EU")
        call_body = client.request.call_args[1]["body"]
        self.assertEqual(call_body["name"], "Full")
        self.assertEqual(call_body["organizationId"], "org1")
        self.assertEqual(call_body["dataResidency"], "EU")

    def test_update_workspace(self):
        client = _make_client({"workspaceId": "ws1", "name": "Updated"})
        api.update_workspace(client, "ws1", name="Updated")
        client.request.assert_called_once_with("PATCH", "/workspaces/ws1", body={"name": "Updated"})

    def test_update_workspace_strips_none(self):
        client = _make_client({})
        api.update_workspace(client, "ws1", name="X", data_residency=None)
        call_body = client.request.call_args[1]["body"]
        self.assertNotIn("dataResidency", call_body)

    def test_delete_workspace(self):
        client = _make_client({})
        api.delete_workspace(client, "ws1")
        client.request.assert_called_once_with("DELETE", "/workspaces/ws1")

    def test_set_oauth_credentials(self):
        client = _make_client({"credentialId": "cred1"})
        api.set_oauth_credentials(client, "ws1", "source", "my-oauth", {"token": "abc"})
        client.request.assert_called_once_with(
            "PUT",
            "/workspaces/ws1/oauthCredentials",
            body={"actorType": "source", "name": "my-oauth", "configuration": {"token": "abc"}},
        )


class TestWorkspacesCommands(unittest.TestCase):
    def _run(self, action: str, extra_attrs: dict | None = None, client=None) -> tuple[int, MagicMock]:
        if client is None:
            client = _make_client({})
        args = argparse.Namespace(workspaces_action=action, format="json")
        if extra_attrs:
            for k, v in extra_attrs.items():
                setattr(args, k, v)
        ctx = _make_context(client)
        with patch("airbyte_api_cli.plugins.workspaces.commands.output") as mock_out:
            code = _handle(args, ctx)
        return code, mock_out

    def test_list_calls_api(self):
        client = _make_client({"data": [{"workspaceId": "ws1", "name": "A"}]})
        code, mock_out = self._run("list", client=client)
        self.assertEqual(code, 0)
        mock_out.assert_called_once()

    def test_get_calls_api(self):
        client = _make_client({"workspaceId": "ws1"})
        code, mock_out = self._run("get", {"workspace_id": "ws1"}, client=client)
        self.assertEqual(code, 0)
        client.request.assert_called_once_with("GET", "/workspaces/ws1")

    def test_create_calls_api(self):
        client = _make_client({"workspaceId": "ws_new"})
        code, _ = self._run(
            "create",
            {"name": "New", "organization_id": None, "data_residency": None},
            client=client,
        )
        self.assertEqual(code, 0)

    def test_update_calls_api(self):
        client = _make_client({"workspaceId": "ws1"})
        code, _ = self._run("update", {"workspace_id": "ws1", "name": "Upd", "data_residency": None}, client=client)
        self.assertEqual(code, 0)

    def test_delete_calls_api(self):
        client = _make_client({})
        code, mock_out = self._run("delete", {"workspace_id": "ws1"}, client=client)
        self.assertEqual(code, 0)
        mock_out.assert_called_once()

    def test_oauth_valid_config(self):
        client = _make_client({})
        args = argparse.Namespace(
            workspaces_action="oauth",
            format="json",
            workspace_id="ws1",
            actor_type="source",
            name="cred",
            config='{"token": "abc"}',
        )
        ctx = _make_context(client)
        with patch("airbyte_api_cli.plugins.workspaces.commands.output"):
            code = _handle(args, ctx)
        self.assertEqual(code, 0)

    def test_oauth_invalid_json_returns_error(self):
        client = _make_client({})
        args = argparse.Namespace(
            workspaces_action="oauth",
            format="json",
            workspace_id="ws1",
            actor_type="source",
            name="cred",
            config="not-json",
        )
        ctx = _make_context(client)
        with patch("airbyte_api_cli.plugins.workspaces.commands.error") as mock_err:
            code = _handle(args, ctx)
        self.assertEqual(code, 1)
        mock_err.assert_called_once()

    def test_no_action_returns_1(self):
        code, _ = self._run(None)
        self.assertEqual(code, 1)

    def test_register_commands_adds_parser(self):
        Registry.reset()
        import argparse as ap
        root = ap.ArgumentParser()
        sub = root.add_subparsers()
        register_commands(sub, {})
        args = root.parse_args(["workspaces", "list"])
        self.assertEqual(args.workspaces_action, "list")


if __name__ == "__main__":
    unittest.main()
