"""CLI commands for the streams plugin."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output

from . import api


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `streams` subcommand."""
    parser = subparsers.add_parser("streams", help="Inspect Airbyte streams")
    sub = parser.add_subparsers(dest="streams_action")

    # get
    get_cmd = sub.add_parser("get", help="Get a stream by ID")
    get_cmd.add_argument("--id", required=True, dest="stream_id", help="Stream ID")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    client = context["get_client"]()
    fmt = context.get("format", "json")
    action = args.streams_action

    if action == "get":
        data = api.get_stream(client, args.stream_id)
        output(data, fmt=fmt)
        return 0

    error("usage", "No streams action specified.")
    return 1
