"""CLI commands for organizations."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output
from airbyte_api_cli.core.utils import resolve_json_arg


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `organizations` subcommand tree."""
    parser = subparsers.add_parser("organizations", help="Manage organizations")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List organizations")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    # oauth
    oauth_cmd = sub.add_parser("oauth", help="Update OAuth credentials for an organization")
    oauth_cmd.add_argument("--id", required=True, dest="organization_id")
    oauth_cmd.add_argument(
        "--data", required=True, help="OAuth credentials as JSON or @file.json"
    )

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch organizations subcommand."""
    from .api import OrganizationsApi

    client = context["get_client"]()
    api = OrganizationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        if getattr(args, "fetch_all", False):
            from airbyte_api_cli.core.utils import paginate_all
            data = paginate_all(api.list, limit=args.limit)
            output(data, fmt)
        else:
            result = api.list(limit=args.limit, offset=args.offset)
            output(result.data, fmt)

    elif args.action == "oauth":
        data = resolve_json_arg(args.data)
        result = api.update_oauth_credentials(args.organization_id, data)
        output(result, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
