"""CLI commands for users."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `users` subcommand tree."""
    parser = subparsers.add_parser("users", help="Manage users")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List users in an organization")
    list_cmd.add_argument(
        "--organization-id", required=True, dest="organization_id",
        help="Organization ID to list users for",
    )
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.add_argument("--all", action="store_true", dest="fetch_all", help="Fetch all pages")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch users subcommand."""
    from .api import UsersApi

    client = context["get_client"]()
    api = UsersApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        if getattr(args, "fetch_all", False):
            from airbyte_api_cli.core.utils import paginate_all
            data = paginate_all(api.list, limit=args.limit, organization_id=args.organization_id)
            output(data, fmt)
        else:
            result = api.list(
                organization_id=args.organization_id,
                limit=args.limit,
                offset=args.offset,
            )
            output(result.data, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
