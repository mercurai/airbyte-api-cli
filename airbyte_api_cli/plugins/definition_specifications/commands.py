"""CLI commands for definition_specifications."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("definition_specifications", help="Get connector config specifications")
    sub = parser.add_subparsers(dest="action")

    src = sub.add_parser("source", help="Get source definition specification")
    src.add_argument("--id", required=True, dest="definition_id")
    src.add_argument("--workspace-id", required=True, dest="workspace_id")

    dst = sub.add_parser("destination", help="Get destination definition specification")
    dst.add_argument("--id", required=True, dest="definition_id")
    dst.add_argument("--workspace-id", required=True, dest="workspace_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import DefinitionSpecificationsApi

    client = context["get_config_client"]()
    api = DefinitionSpecificationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "source":
        result = api.get_source_spec(args.definition_id, args.workspace_id)
        output(result, fmt)
    elif args.action == "destination":
        result = api.get_destination_spec(args.definition_id, args.workspace_id)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
