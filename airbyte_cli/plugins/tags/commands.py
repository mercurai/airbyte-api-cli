"""CLI commands for tags."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import strip_none


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `tags` subcommand."""
    parser = subparsers.add_parser("tags", help="Manage tags")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List tags")
    list_cmd.add_argument("--workspace-id", dest="workspace_id")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    # get
    get_cmd = sub.add_parser("get", help="Get tag details")
    get_cmd.add_argument("--id", required=True, dest="tag_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a tag")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--color")
    create_cmd.add_argument("--workspace-id", dest="workspace_id")

    # update
    update_cmd = sub.add_parser("update", help="Update a tag")
    update_cmd.add_argument("--id", required=True, dest="tag_id")
    update_cmd.add_argument("--name")
    update_cmd.add_argument("--color")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a tag")
    delete_cmd.add_argument("--id", required=True, dest="tag_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import TagsApi

    client = context["get_client"]()
    api = TagsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        params = strip_none({
            "workspaceId": getattr(args, "workspace_id", None),
            "limit": args.limit,
            "offset": args.offset,
        })
        result = api.list(**params)
        output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.tag_id)
        output(result, fmt)

    elif args.action == "create":
        data = strip_none({
            "name": args.name,
            "color": args.color,
            "workspaceId": getattr(args, "workspace_id", None),
        })
        result = api.create(data)
        output(result, fmt)

    elif args.action == "update":
        data = strip_none({
            "name": args.name,
            "color": args.color,
        })
        result = api.update(args.tag_id, data)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.tag_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
