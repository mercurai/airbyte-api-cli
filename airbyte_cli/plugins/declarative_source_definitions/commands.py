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
    list_cmd = sub.add_parser("list", help="List manifest versions")
    list_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    list_cmd.add_argument(
        "--source-definition-id", required=True, dest="source_definition_id"
    )

    # create
    create_cmd = sub.add_parser("create", help="Create a declarative manifest")
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument(
        "--source-definition-id", required=True, dest="source_definition_id"
    )
    create_cmd.add_argument(
        "--manifest", required=True, help="JSON manifest string or @file.json"
    )
    create_cmd.add_argument(
        "--spec", default="{}", help="JSON spec string or @file.json"
    )
    create_cmd.add_argument("--description", default="")
    create_cmd.add_argument("--version", type=int, default=0)

    # update
    update_cmd = sub.add_parser("update", help="Update the active manifest")
    update_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    update_cmd.add_argument(
        "--source-definition-id", required=True, dest="source_definition_id"
    )
    update_cmd.add_argument(
        "--manifest", required=True, help="JSON manifest string or @file.json"
    )
    update_cmd.add_argument(
        "--spec", default="{}", help="JSON spec string or @file.json"
    )
    update_cmd.add_argument("--description", default="")
    update_cmd.add_argument("--version", type=int, default=0)

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch declarative_source_definitions subcommand."""
    from .api import DeclarativeSourceDefinitionsApi

    client = context["get_config_client"]()
    api = DeclarativeSourceDefinitionsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list_manifests(args.workspace_id, args.source_definition_id)
        output(result.data, fmt)

    elif args.action == "create":
        manifest = resolve_json_arg(args.manifest)
        spec = resolve_json_arg(args.spec)
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id=args.workspace_id,
            source_definition_id=args.source_definition_id,
            manifest=manifest,
            spec=spec,
            description=args.description,
            version=args.version,
        )
        result = api.create_manifest(payload)
        output(result, fmt)

    elif args.action == "update":
        manifest = resolve_json_arg(args.manifest)
        spec = resolve_json_arg(args.spec)
        payload = DeclarativeSourceDefinitionCreate(
            workspace_id=args.workspace_id,
            source_definition_id=args.source_definition_id,
            manifest=manifest,
            spec=spec,
            description=args.description,
            version=args.version,
        )
        result = api.update_manifest(payload)
        output(result, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
