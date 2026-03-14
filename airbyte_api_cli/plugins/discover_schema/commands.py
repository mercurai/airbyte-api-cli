"""CLI commands for discover_schema."""
from __future__ import annotations
import argparse
from typing import Any
from airbyte_api_cli.core.output import error, output

def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("discover_schema", help="Discover source catalog schema")
    parser.add_argument("--source-id", required=True, dest="source_id")
    parser.add_argument("--disable-cache", action="store_true", default=False, dest="disable_cache")
    parser.set_defaults(handler=_handle)

def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import DiscoverSchemaApi
    client = context["get_config_client"]()
    api = DiscoverSchemaApi(client)
    fmt = context.get("format", "json")
    result = api.discover(args.source_id, disable_cache=args.disable_cache)
    output(result, fmt)
    return 0
