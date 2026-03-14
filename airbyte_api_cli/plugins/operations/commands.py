"""CLI commands for operations."""
from __future__ import annotations
import argparse
from typing import Any
from airbyte_api_cli.core.output import error, output
from airbyte_api_cli.core.utils import resolve_json_arg

def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("operations", help="Manage connection operations")
    sub = parser.add_subparsers(dest="action")

    list_cmd = sub.add_parser("list", help="List operations for a connection")
    list_cmd.add_argument("--connection-id", required=True, dest="connection_id")

    get_cmd = sub.add_parser("get", help="Get an operation")
    get_cmd.add_argument("--id", required=True, dest="operation_id")

    create_cmd = sub.add_parser("create", help="Create an operation")
    create_cmd.add_argument("--connection-id", required=True, dest="connection_id")
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--config", required=True, help="JSON operator config or @file.json")

    update_cmd = sub.add_parser("update", help="Update an operation")
    update_cmd.add_argument("--id", required=True, dest="operation_id")
    update_cmd.add_argument("--name", required=True)
    update_cmd.add_argument("--config", required=True, help="JSON operator config or @file.json")

    delete_cmd = sub.add_parser("delete", help="Delete an operation")
    delete_cmd.add_argument("--id", required=True, dest="operation_id")

    check_cmd = sub.add_parser("check", help="Check an operator configuration")
    check_cmd.add_argument("--config", required=True, help="JSON operator config or @file.json")

    parser.set_defaults(handler=_handle)

def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import OperationsApi
    client = context["get_config_client"]()
    api = OperationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list(args.connection_id)
        output(result.data, fmt)
    elif args.action == "get":
        result = api.get(args.operation_id)
        output(result, fmt)
    elif args.action == "create":
        config = resolve_json_arg(args.config)
        result = api.create(args.connection_id, args.workspace_id, args.name, config)
        output(result, fmt)
    elif args.action == "update":
        config = resolve_json_arg(args.config)
        result = api.update(args.operation_id, args.name, config)
        output(result, fmt)
    elif args.action == "delete":
        api.delete(args.operation_id)
    elif args.action == "check":
        config = resolve_json_arg(args.config)
        result = api.check(config)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
