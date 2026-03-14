"""CLI commands for check_connection."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("check_connection", help="Test source/destination connectivity")
    sub = parser.add_subparsers(dest="action")

    source_cmd = sub.add_parser("source", help="Check source connection")
    source_cmd.add_argument("--id", required=True, dest="source_id")

    dest_cmd = sub.add_parser("destination", help="Check destination connection")
    dest_cmd.add_argument("--id", required=True, dest="destination_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import CheckConnectionApi

    client = context["get_config_client"]()
    api = CheckConnectionApi(client)
    fmt = context.get("format", "json")

    if args.action == "source":
        result = api.check_source(args.source_id)
        output(result, fmt)
    elif args.action == "destination":
        result = api.check_destination(args.destination_id)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
