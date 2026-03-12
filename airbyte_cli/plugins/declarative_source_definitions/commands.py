"""CLI commands for declarative source definitions."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import resolve_json_arg

from .models import DeclarativeSourceDefinitionCreate


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `declarative_source_definitions` subcommand tree."""
    parser = subparsers.add_parser(
        "declarative_source_definitions",
        help="Manage declarative (low-code) source definitions",
    )
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List declarative source definitions")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    # get
    get_cmd = sub.add_parser("get", help="Get declarative source definition details")
    get_cmd.add_argument("--id", required=True, dest="definition_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a declarative source definition")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument(
        "--manifest", required=True, help="JSON manifest string or @file.json"
    )
    create_cmd.add_argument("--description", default="")

    # update (PUT -- full replace)
    update_cmd = sub.add_parser(
        "update", help="Replace a declarative source definition (PUT)"
    )
    update_cmd.add_argument("--id", required=True, dest="definition_id")
    update_cmd.add_argument("--name", required=True)
    update_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    update_cmd.add_argument(
        "--manifest", required=True, help="JSON manifest string or @file.json"
    )
    update_cmd.add_argument("--description", default="")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a declarative source definition")
    delete_cmd.add_argument("--id", required=True, dest="definition_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch declarative_source_definitions subcommand."""
    from .api import DeclarativeSourceDefinitionsApi

    client = context["get_client"]()
    api = DeclarativeSourceDefinitionsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list(limit=args.limit, offset=args.offset)
        output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.definition_id)
        output(result, fmt)

    elif args.action == "create":
        manifest = resolve_json_arg(args.manifest)
        payload = DeclarativeSourceDefinitionCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            manifest=manifest,
            description=args.description,
        )
        result = api.create(payload)
        output(result, fmt)

    elif args.action == "update":
        manifest = resolve_json_arg(args.manifest)
        payload = DeclarativeSourceDefinitionCreate(
            name=args.name,
            workspace_id=args.workspace_id,
            manifest=manifest,
            description=args.description,
        )
        result = api.update(args.definition_id, payload)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.definition_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
