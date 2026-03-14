"""CLI commands for web_backend."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("web_backend", help="Enriched connection views and workspace state")
    sub = parser.add_subparsers(dest="action")

    list_cmd = sub.add_parser("list", help="List connections (enriched)")
    list_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")

    get_cmd = sub.add_parser("get", help="Get connection (enriched)")
    get_cmd.add_argument("--id", required=True, dest="connection_id")
    get_cmd.add_argument("--with-refreshed-catalog", action="store_true", default=False, dest="with_refreshed_catalog")

    sub.add_parser("check-updates", help="Check for definition updates")

    ws_cmd = sub.add_parser("workspace-state", help="Get workspace state")
    ws_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import WebBackendApi

    client = context["get_config_client"]()
    api = WebBackendApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list_connections(args.workspace_id)
        output(result.data, fmt)
    elif args.action == "get":
        result = api.get_connection(args.connection_id, args.with_refreshed_catalog)
        output(result, fmt)
    elif args.action == "check-updates":
        result = api.check_updates()
        output(result, fmt)
    elif args.action == "workspace-state":
        result = api.workspace_state(args.workspace_id)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
