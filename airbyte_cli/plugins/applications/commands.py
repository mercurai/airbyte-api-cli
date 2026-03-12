"""CLI commands for applications."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import strip_none


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `applications` subcommand."""
    parser = subparsers.add_parser("applications", help="Manage applications")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List applications")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    # get
    get_cmd = sub.add_parser("get", help="Get application details")
    get_cmd.add_argument("--id", required=True, dest="application_id")

    # create
    create_cmd = sub.add_parser("create", help="Create an application")
    create_cmd.add_argument("--name", required=True)

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete an application")
    delete_cmd.add_argument("--id", required=True, dest="application_id")

    # token
    token_cmd = sub.add_parser("token", help="Generate an access token for an application")
    token_cmd.add_argument("--id", required=True, dest="application_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import ApplicationsApi

    client = context["get_client"]()
    api = ApplicationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        if getattr(args, "fetch_all", False):
            from airbyte_cli.core.utils import paginate_all
            data = paginate_all(api.list, limit=args.limit)
            output(data, fmt)
        else:
            params = strip_none({
                "limit": args.limit,
                "offset": args.offset,
            })
            result = api.list(**params)
            output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.application_id)
        output(result, fmt)

    elif args.action == "create":
        result = api.create({"name": args.name})
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.application_id)

    elif args.action == "token":
        result = api.token(args.application_id)
        output(result, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
