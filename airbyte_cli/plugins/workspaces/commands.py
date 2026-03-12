"""CLI commands for the workspaces plugin."""

from __future__ import annotations

import argparse
import json
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import resolve_json_arg

from . import api


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `workspaces` subcommand."""
    parser = subparsers.add_parser("workspaces", help="Manage Airbyte workspaces")
    sub = parser.add_subparsers(dest="workspaces_action")

    # list
    sub.add_parser("list", help="List all workspaces")

    # get
    get_cmd = sub.add_parser("get", help="Get a workspace by ID")
    get_cmd.add_argument("--id", required=True, dest="workspace_id", help="Workspace ID")

    # create
    create_cmd = sub.add_parser("create", help="Create a new workspace")
    create_cmd.add_argument("--name", required=True, help="Workspace name")
    create_cmd.add_argument("--organization-id", dest="organization_id", help="Organization ID")
    create_cmd.add_argument("--data-residency", dest="data_residency", help="Data residency region")

    # update
    update_cmd = sub.add_parser("update", help="Update a workspace")
    update_cmd.add_argument("--id", required=True, dest="workspace_id", help="Workspace ID")
    update_cmd.add_argument("--name", help="New workspace name")
    update_cmd.add_argument("--data-residency", dest="data_residency", help="Data residency region")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a workspace")
    delete_cmd.add_argument("--id", required=True, dest="workspace_id", help="Workspace ID")

    # oauth
    oauth_cmd = sub.add_parser("oauth", help="Set OAuth credentials for a workspace")
    oauth_cmd.add_argument("--id", required=True, dest="workspace_id", help="Workspace ID")
    oauth_cmd.add_argument(
        "--actor-type",
        required=True,
        dest="actor_type",
        choices=["source", "destination"],
        help="Actor type",
    )
    oauth_cmd.add_argument("--name", required=True, help="Credential name")
    oauth_cmd.add_argument("--config", required=True, help="JSON config string or @filepath")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    client = context["get_client"]()
    fmt = context.get("format", "json")
    action = args.workspaces_action

    if action == "list":
        data = api.list_workspaces(client)
        output(data, fmt=fmt, columns=["workspaceId", "name", "dataResidency"])
        return 0

    if action == "get":
        data = api.get_workspace(client, args.workspace_id)
        output(data, fmt=fmt)
        return 0

    if action == "create":
        data = api.create_workspace(
            client,
            name=args.name,
            organization_id=getattr(args, "organization_id", None),
            data_residency=getattr(args, "data_residency", None),
        )
        output(data, fmt=fmt)
        return 0

    if action == "update":
        data = api.update_workspace(
            client,
            workspace_id=args.workspace_id,
            name=getattr(args, "name", None),
            data_residency=getattr(args, "data_residency", None),
        )
        output(data, fmt=fmt)
        return 0

    if action == "delete":
        api.delete_workspace(client, args.workspace_id)
        output({"deleted": args.workspace_id}, fmt=fmt)
        return 0

    if action == "oauth":
        try:
            config = resolve_json_arg(args.config)
        except (ValueError, FileNotFoundError) as exc:
            error("config", str(exc))
            return 1
        data = api.set_oauth_credentials(
            client,
            workspace_id=args.workspace_id,
            actor_type=args.actor_type,
            name=args.name,
            configuration=config,
        )
        output(data, fmt=fmt)
        return 0

    error("usage", "No workspaces action specified.")
    return 1
