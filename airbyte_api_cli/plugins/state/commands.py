"""CLI commands for state."""
from __future__ import annotations
import argparse
from typing import Any
from airbyte_api_cli.core.output import error, output
from airbyte_api_cli.core.utils import resolve_json_arg

def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("state", help="Manage connection sync state")
    sub = parser.add_subparsers(dest="action")

    get_cmd = sub.add_parser("get", help="Get connection state")
    get_cmd.add_argument("--connection-id", required=True, dest="connection_id")

    set_cmd = sub.add_parser("set", help="Create or update connection state")
    set_cmd.add_argument("--connection-id", required=True, dest="connection_id")
    set_cmd.add_argument("--state", required=True, help="JSON state string or @file.json")

    parser.set_defaults(handler=_handle)

def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import StateApi
    client = context["get_config_client"]()
    api = StateApi(client)
    fmt = context.get("format", "json")

    if args.action == "get":
        result = api.get(args.connection_id)
        output(result, fmt)
    elif args.action == "set":
        state_data = resolve_json_arg(args.state)
        result = api.create_or_update(args.connection_id, state_data)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
