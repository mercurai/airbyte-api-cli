"""CLI commands for destinations."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import resolve_json_arg

from .models import DestinationCreate


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `destinations` subcommand tree."""
    parser = subparsers.add_parser("destinations", help="Manage destinations")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List destinations")
    list_cmd.add_argument("--workspace-id", dest="workspace_id", help="Filter by workspace ID")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    # get
    get_cmd = sub.add_parser("get", help="Get destination details")
    get_cmd.add_argument("--id", required=True, dest="destination_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a destination")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument("--type", required=True, dest="destination_type")
    create_cmd.add_argument(
        "--config", required=True, dest="configuration",
        help="Connector configuration as JSON string or @file.json",
    )
    create_cmd.add_argument("--definition-id", dest="definition_id", default="")

    # update (PATCH)
    update_cmd = sub.add_parser("update", help="Partially update a destination (PATCH)")
    update_cmd.add_argument("--id", required=True, dest="destination_id")
    update_cmd.add_argument(
        "--data", required=True, help="Partial update fields as JSON or @file.json"
    )

    # replace (PUT)
    replace_cmd = sub.add_parser("replace", help="Replace a destination (PUT)")
    replace_cmd.add_argument("--id", required=True, dest="destination_id")
    replace_cmd.add_argument("--name", required=True)
    replace_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    replace_cmd.add_argument("--type", required=True, dest="destination_type")
    replace_cmd.add_argument(
        "--config", required=True, dest="configuration",
        help="Connector configuration as JSON string or @file.json",
    )
    replace_cmd.add_argument("--definition-id", dest="definition_id", default="")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a destination")
    delete_cmd.add_argument("--id", required=True, dest="destination_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch destinations subcommand."""
    from .api import DestinationsApi

    client = context["get_client"]()
    api = DestinationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        workspace_ids = [args.workspace_id] if args.workspace_id else None
        if getattr(args, "fetch_all", False):
            from airbyte_cli.core.utils import paginate_all
            data = paginate_all(api.list, limit=args.limit, workspace_ids=workspace_ids)
            output(data, fmt)
        else:
            result = api.list(workspace_ids=workspace_ids, limit=args.limit, offset=args.offset)
            output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.destination_id)
        output(result, fmt)

    elif args.action == "create":
        configuration = resolve_json_arg(args.configuration)
        payload = DestinationCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            destination_type=args.destination_type,
            configuration=configuration,
            definition_id=args.definition_id,
        )
        result = api.create(payload)
        output(result, fmt)

    elif args.action == "update":
        data = resolve_json_arg(args.data)
        result = api.update(args.destination_id, data)
        output(result, fmt)

    elif args.action == "replace":
        configuration = resolve_json_arg(args.configuration)
        payload = DestinationCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            destination_type=args.destination_type,
            configuration=configuration,
            definition_id=args.definition_id,
        )
        result = api.replace(args.destination_id, payload)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.destination_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
