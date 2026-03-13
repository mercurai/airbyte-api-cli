"""CLI commands for health check."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import output


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `health` subcommand."""
    parser = subparsers.add_parser("health", help="Check API health status")
    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    client = context["get_client"]()
    result = client.request("GET", "health")
    fmt = context.get("format", "json")
    output(result, fmt)
    return 0
