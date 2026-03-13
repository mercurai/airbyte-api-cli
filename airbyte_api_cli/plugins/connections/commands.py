"""CLI commands for connections."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output
from airbyte_api_cli.core.utils import resolve_json_arg, strip_none


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `connections` subcommand."""
    parser = subparsers.add_parser("connections", help="Manage connections")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List connections")
    list_cmd.add_argument("--workspace-id", dest="workspace_id")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    # get
    get_cmd = sub.add_parser("get", help="Get connection details")
    get_cmd.add_argument("--id", required=True, dest="connection_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a connection")
    create_cmd.add_argument("--source-id", required=True, dest="source_id")
    create_cmd.add_argument("--destination-id", required=True, dest="destination_id")
    create_cmd.add_argument("--name")
    create_cmd.add_argument("--schedule", help="JSON: {scheduleType, cronExpression}")
    create_cmd.add_argument("--streams", help="JSON stream configuration")
    create_cmd.add_argument(
        "--status", choices=["active", "inactive", "deprecated"]
    )
    create_cmd.add_argument(
        "--namespace",
        dest="namespace_definition",
        choices=["source", "destination", "custom_format"],
    )
    create_cmd.add_argument("--data-residency", dest="data_residency")
    create_cmd.add_argument("--prefix")

    # update
    update_cmd = sub.add_parser("update", help="Update a connection")
    update_cmd.add_argument("--id", required=True, dest="connection_id")
    update_cmd.add_argument("--data", required=True, help="JSON or @file.json")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a connection")
    delete_cmd.add_argument("--id", required=True, dest="connection_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import ConnectionsApi

    api = ConnectionsApi(context["get_client"]())
    fmt = context.get("format", "json")

    if args.action == "list":
        if getattr(args, "fetch_all", False):
            from airbyte_api_cli.core.utils import paginate_all
            extra = strip_none({"workspaceId": getattr(args, "workspace_id", None)})
            data = paginate_all(api.list, limit=args.limit, **extra)
            output(data, fmt)
        else:
            params = strip_none({
                "workspaceId": getattr(args, "workspace_id", None),
                "limit": args.limit,
                "offset": args.offset,
            })
            result = api.list(**params)
            output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.connection_id)
        output(result, fmt)

    elif args.action == "create":
        data: dict[str, Any] = {
            "sourceId": args.source_id,
            "destinationId": args.destination_id,
        }
        if args.name:
            data["name"] = args.name
        if args.status:
            data["status"] = args.status
        if args.namespace_definition:
            data["namespaceDefinition"] = args.namespace_definition
        if args.data_residency:
            data["dataResidency"] = args.data_residency
        if args.prefix:
            data["prefix"] = args.prefix
        if args.schedule:
            data["schedule"] = resolve_json_arg(args.schedule)
        if args.streams:
            data["configurations"] = {"streams": resolve_json_arg(args.streams)}
        result = api.create(data)
        output(result, fmt)

    elif args.action == "update":
        data = resolve_json_arg(args.data)
        result = api.update(args.connection_id, data)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.connection_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
