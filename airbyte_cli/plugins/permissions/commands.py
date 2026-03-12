"""CLI commands for the permissions plugin."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output

from . import api


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `permissions` subcommand."""
    parser = subparsers.add_parser("permissions", help="Manage Airbyte permissions")
    sub = parser.add_subparsers(dest="permissions_action")

    # list
    list_cmd = sub.add_parser("list", help="List permissions")
    list_cmd.add_argument("--user-id", dest="user_id", help="Filter by user ID")
    list_cmd.add_argument("--organization-id", dest="organization_id", help="Filter by organization ID")

    # get
    get_cmd = sub.add_parser("get", help="Get a permission by ID")
    get_cmd.add_argument("--id", required=True, dest="permission_id", help="Permission ID")

    # create
    create_cmd = sub.add_parser("create", help="Create a new permission")
    create_cmd.add_argument("--permission-type", required=True, dest="permission_type", help="Permission type")
    create_cmd.add_argument("--user-id", required=True, dest="user_id", help="User ID")
    create_cmd.add_argument("--workspace-id", dest="workspace_id", help="Workspace ID")
    create_cmd.add_argument("--organization-id", dest="organization_id", help="Organization ID")

    # update
    update_cmd = sub.add_parser("update", help="Update a permission")
    update_cmd.add_argument("--id", required=True, dest="permission_id", help="Permission ID")
    update_cmd.add_argument("--permission-type", dest="permission_type", help="New permission type")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a permission")
    delete_cmd.add_argument("--id", required=True, dest="permission_id", help="Permission ID")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    client = context["get_client"]()
    fmt = context.get("format", "json")
    action = args.permissions_action

    if action == "list":
        data = api.list_permissions(
            client,
            user_id=getattr(args, "user_id", None),
            organization_id=getattr(args, "organization_id", None),
        )
        output(data, fmt=fmt, columns=["permissionId", "permissionType", "userId", "workspaceId"])
        return 0

    if action == "get":
        data = api.get_permission(client, args.permission_id)
        output(data, fmt=fmt)
        return 0

    if action == "create":
        data = api.create_permission(
            client,
            permission_type=args.permission_type,
            user_id=args.user_id,
            workspace_id=getattr(args, "workspace_id", None),
            organization_id=getattr(args, "organization_id", None),
        )
        output(data, fmt=fmt)
        return 0

    if action == "update":
        data = api.update_permission(
            client,
            permission_id=args.permission_id,
            permission_type=getattr(args, "permission_type", None),
        )
        output(data, fmt=fmt)
        return 0

    if action == "delete":
        api.delete_permission(client, args.permission_id)
        output({"deleted": args.permission_id}, fmt=fmt)
        return 0

    error("usage", "No permissions action specified.")
    return 1
