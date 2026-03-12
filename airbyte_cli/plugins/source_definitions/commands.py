"""CLI commands for source definitions."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output

from .models import SourceDefinitionCreate


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `source_definitions` subcommand tree."""
    parser = subparsers.add_parser("source_definitions", help="Manage source definitions")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List source definitions")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    # get
    get_cmd = sub.add_parser("get", help="Get source definition details")
    get_cmd.add_argument("--id", required=True, dest="definition_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a source definition")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--docker-repository", required=True, dest="docker_repository")
    create_cmd.add_argument("--docker-image-tag", required=True, dest="docker_image_tag")
    create_cmd.add_argument("--documentation-url", dest="documentation_url", default="")

    # update (PUT — full replace)
    update_cmd = sub.add_parser("update", help="Replace a source definition (PUT)")
    update_cmd.add_argument("--id", required=True, dest="definition_id")
    update_cmd.add_argument("--name", required=True)
    update_cmd.add_argument("--docker-repository", required=True, dest="docker_repository")
    update_cmd.add_argument("--docker-image-tag", required=True, dest="docker_image_tag")
    update_cmd.add_argument("--documentation-url", dest="documentation_url", default="")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a source definition")
    delete_cmd.add_argument("--id", required=True, dest="definition_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch source_definitions subcommand."""
    from .api import SourceDefinitionsApi

    client = context["get_client"]()
    api = SourceDefinitionsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list(limit=args.limit, offset=args.offset)
        output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.definition_id)
        output(result, fmt)

    elif args.action == "create":
        payload = SourceDefinitionCreate(
            name=args.name,
            docker_repository=args.docker_repository,
            docker_image_tag=args.docker_image_tag,
            documentation_url=args.documentation_url,
        )
        result = api.create(payload)
        output(result, fmt)

    elif args.action == "update":
        payload = SourceDefinitionCreate(
            name=args.name,
            docker_repository=args.docker_repository,
            docker_image_tag=args.docker_image_tag,
            documentation_url=args.documentation_url,
        )
        result = api.update(args.definition_id, payload)
        output(result, fmt)

    elif args.action == "delete":
        api.delete(args.definition_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
