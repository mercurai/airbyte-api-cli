"""CLI commands for sources."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import resolve_json_arg

from .models import SourceCreate


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `sources` subcommand tree."""
    parser = subparsers.add_parser("sources", help="Manage sources")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List sources")
    list_cmd.add_argument("--workspace-id", dest="workspace_id", help="Filter by workspace ID")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    # get
    get_cmd = sub.add_parser("get", help="Get source details")
    get_cmd.add_argument("--id", required=True, dest="source_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a source")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument("--type", required=True, dest="source_type")
    create_cmd.add_argument(
        "--config", required=True, dest="configuration",
        help="Connector configuration as JSON string or @file.json",
    )
    create_cmd.add_argument("--definition-id", dest="definition_id", default="")

    # update (PATCH)
    update_cmd = sub.add_parser("update", help="Partially update a source (PATCH)")
    update_cmd.add_argument("--id", required=True, dest="source_id")
    update_cmd.add_argument(
        "--data", required=True, help="Partial update fields as JSON or @file.json"
    )

    # replace (PUT)
    replace_cmd = sub.add_parser("replace", help="Replace a source (PUT)")
    replace_cmd.add_argument("--id", required=True, dest="source_id")
    replace_cmd.add_argument("--name", required=True)
    replace_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    replace_cmd.add_argument("--type", required=True, dest="source_type")
    replace_cmd.add_argument(
        "--config", required=True, dest="configuration",
        help="Connector configuration as JSON string or @file.json",
    )
    replace_cmd.add_argument("--definition-id", dest="definition_id", default="")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a source")
    delete_cmd.add_argument("--id", required=True, dest="source_id")

    # oauth
    oauth_cmd = sub.add_parser("oauth", help="Initiate OAuth for a source")
    oauth_cmd.add_argument(
        "--data", required=True, help="OAuth payload as JSON or @file.json"
    )

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch sources subcommand."""
    from .api import SourcesApi

    client = context["get_client"]()
    api = SourcesApi(client)
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
        result = api.get(args.source_id)
        output(result, fmt)

    elif args.action == "create":
        configuration = resolve_json_arg(args.configuration)
        payload = SourceCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            source_type=args.source_type,
            configuration=configuration,
            definition_id=args.definition_id,
        )
        result = api.create(payload)
        output(result, fmt)

    elif args.action == "update":
        data = resolve_json_arg(args.data)
        result = api.update(args.source_id, data)
        output(result, fmt)

    elif args.action == "replace":
        configuration = resolve_json_arg(args.configuration)
        payload = SourceCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            source_type=args.source_type,
            configuration=configuration,
            definition_id=args.definition_id,
        )
        result = api.replace(args.source_id, payload)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.source_id)

    elif args.action == "oauth":
        data = resolve_json_arg(args.data)
        result = api.oauth(data)
        output(result, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
