"""Tests for the permissions plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.plugins.permissions import api
from airbyte_api_cli.plugins.permissions.commands import register_commands, _handle
from airbyte_api_cli.plugins.permissions.models import Permission


def _make_client(return_value=None):
    client = MagicMock()
    client.request.return_value = return_value or {}
    return client


def _make_context(client=None):
    c = client or _make_client()
    return {"get_client": lambda: c, "format": "json"}


class TestPermissionModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "permissionId": "p1",
            "permissionType": "workspace_admin",
            "userId": "u1",
            "workspaceId": "ws1",
            "organizationId": "org1",
        }
        perm = Permission.from_dict(data)
        self.assertEqual(perm.permissionId, "p1")
        self.assertEqual(perm.permissionType, "workspace_admin")
        self.assertEqual(perm.workspaceId, "ws1")
        self.assertEqual(perm.organizationId, "org1")

    def test_from_dict_minimal(self):
        data = {"permissionId": "p2", "permissionType": "workspace_reader", "userId": "u2"}
        perm = Permission.from_dict(data)
        self.assertIsNone(perm.workspaceId)
        self.assertIsNone(perm.organizationId)

    def test_to_dict_roundtrip(self):
        data = {
            "permissionId": "p3",
            "permissionType": "workspace_editor",
            "userId": "u3",
            "workspaceId": "ws3",
            "organizationId": None,
        }
        perm = Permission.from_dict(data)
        result = perm.to_dict()
        self.assertEqual(result["permissionId"], "p3")
        self.assertEqual(result["workspaceId"], "ws3")
        self.assertIsNone(result["organizationId"])


class TestPermissionsApi(unittest.TestCase):
    def test_list_permissions_no_filters(self):
        client = _make_client({"data": [{"permissionId": "p1"}]})
        result = api.list_permissions(client)
        client.request.assert_called_once_with("GET", "/permissions", params=None)
        self.assertEqual(len(result), 1)

    def test_list_permissions_with_user_filter(self):
        client = _make_client({"data": []})
        api.list_permissions(client, user_id="u1")
        call_kwargs = client.request.call_args[1]
        self.assertEqual(call_kwargs["params"]["userId"], "u1")

    def test_list_permissions_with_org_filter(self):
        client = _make_client({"data": []})
        api.list_permissions(client, organization_id="org1")
        call_kwargs = client.request.call_args[1]
        self.assertEqual(call_kwargs["params"]["organizationId"], "org1")

    def test_list_permissions_empty_response(self):
        client = _make_client({})
        result = api.list_permissions(client)
        self.assertEqual(result, [])

    def test_get_permission(self):
        client = _make_client({"permissionId": "p1"})
        result = api.get_permission(client, "p1")
        client.request.assert_called_once_with("GET", "/permissions/p1")
        self.assertEqual(result["permissionId"], "p1")

    def test_create_permission_minimal(self):
        client = _make_client({"permissionId": "p_new"})
        api.create_permission(client, permission_type="workspace_admin", user_id="u1")
        call_body = client.request.call_args[1]["body"]
        self.assertEqual(call_body["permissionType"], "workspace_admin")
        self.assertEqual(call_body["userId"], "u1")
        self.assertNotIn("workspaceId", call_body)

    def test_create_permission_with_workspace(self):
        client = _make_client({"permissionId": "p_new"})
        api.create_permission(client, "workspace_editor", "u2", workspace_id="ws1")
        call_body = client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")

    def test_create_permission_with_org(self):
        client = _make_client({"permissionId": "p_new"})
        api.create_permission(client, "organization_admin", "u3", organization_id="org1")
        call_body = client.request.call_args[1]["body"]
        self.assertEqual(call_body["organizationId"], "org1")

    def test_update_permission(self):
        client = _make_client({"permissionId": "p1"})
        api.update_permission(client, "p1", permission_type="workspace_reader")
        client.request.assert_called_once_with(
            "PATCH", "/permissions/p1", body={"permissionType": "workspace_reader"}
        )

    def test_update_permission_strips_none(self):
        client = _make_client({})
        api.update_permission(client, "p1", permission_type=None)
        call_body = client.request.call_args[1]["body"]
        self.assertNotIn("permissionType", call_body)

    def test_delete_permission(self):
        client = _make_client({})
        api.delete_permission(client, "p1")
        client.request.assert_called_once_with("DELETE", "/permissions/p1")


class TestPermissionsCommands(unittest.TestCase):
    def _run(self, action: str, extra_attrs: dict | None = None, client=None) -> tuple[int, MagicMock]:
        if client is None:
            client = _make_client({})
        args = argparse.Namespace(permissions_action=action, format="json")
        if extra_attrs:
            for k, v in extra_attrs.items():
                setattr(args, k, v)
        ctx = _make_context(client)
        with patch("airbyte_api_cli.plugins.permissions.commands.output") as mock_out:
            code = _handle(args, ctx)
        return code, mock_out

    def test_list_no_filters(self):
        client = _make_client({"data": []})
        code, mock_out = self._run("list", {"user_id": None, "organization_id": None}, client=client)
        self.assertEqual(code, 0)
        mock_out.assert_called_once()

    def test_list_with_user_id(self):
        client = _make_client({"data": [{"permissionId": "p1"}]})
        code, _ = self._run("list", {"user_id": "u1", "organization_id": None}, client=client)
        self.assertEqual(code, 0)

    def test_get_calls_api(self):
        client = _make_client({"permissionId": "p1"})
        code, mock_out = self._run("get", {"permission_id": "p1"}, client=client)
        self.assertEqual(code, 0)
        client.request.assert_called_once_with("GET", "/permissions/p1")

    def test_create_calls_api(self):
        client = _make_client({"permissionId": "p_new"})
        code, _ = self._run(
            "create",
            {
                "permission_type": "workspace_admin",
                "user_id": "u1",
                "workspace_id": None,
                "organization_id": None,
            },
            client=client,
        )
        self.assertEqual(code, 0)

    def test_update_calls_api(self):
        client = _make_client({"permissionId": "p1"})
        code, _ = self._run("update", {"permission_id": "p1", "permission_type": "workspace_reader"}, client=client)
        self.assertEqual(code, 0)

    def test_delete_calls_api(self):
        client = _make_client({})
        code, mock_out = self._run("delete", {"permission_id": "p1"}, client=client)
        self.assertEqual(code, 0)
        mock_out.assert_called_once()

    def test_no_action_returns_1(self):
        code, _ = self._run(None)
        self.assertEqual(code, 1)

    def test_register_commands_adds_parser(self):
        Registry.reset()
        import argparse as ap
        root = ap.ArgumentParser()
        sub = root.add_subparsers()
        register_commands(sub, {})
        args = root.parse_args(["permissions", "get", "--id", "p1"])
        self.assertEqual(args.permissions_action, "get")
        self.assertEqual(args.permission_id, "p1")

    def test_register_commands_list_with_filters(self):
        Registry.reset()
        import argparse as ap
        root = ap.ArgumentParser()
        sub = root.add_subparsers()
        register_commands(sub, {})
        args = root.parse_args(["permissions", "list", "--user-id", "u1", "--organization-id", "org1"])
        self.assertEqual(args.user_id, "u1")
        self.assertEqual(args.organization_id, "org1")


if __name__ == "__main__":
    unittest.main()
