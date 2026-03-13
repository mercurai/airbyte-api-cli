"""CLI commands for destination definitions."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output

from .models import DestinationDefinitionCreate


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `destination_definitions` subcommand tree."""
    parser = subparsers.add_parser(
        "destination_definitions", help="Manage destination definitions"
    )
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List destination definitions")
    list_cmd.add_argument("--workspace-id", dest="workspace_id", default=None)

    # get
    get_cmd = sub.add_parser("get", help="Get destination definition details")
    get_cmd.add_argument("--id", required=True, dest="definition_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a custom destination definition")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--docker-repository", required=True, dest="docker_repository")
    create_cmd.add_argument("--docker-image-tag", required=True, dest="docker_image_tag")
    create_cmd.add_argument("--documentation-url", dest="documentation_url", default="")
    create_cmd.add_argument("--workspace-id", dest="workspace_id", default=None)

    # update
    update_cmd = sub.add_parser("update", help="Update a destination definition")
    update_cmd.add_argument("--id", required=True, dest="definition_id")
    update_cmd.add_argument("--name", required=True)
    update_cmd.add_argument("--docker-repository", required=True, dest="docker_repository")
    update_cmd.add_argument("--docker-image-tag", required=True, dest="docker_image_tag")
    update_cmd.add_argument("--documentation-url", dest="documentation_url", default="")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a destination definition")
    delete_cmd.add_argument("--id", required=True, dest="definition_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch destination_definitions subcommand."""
    from .api import DestinationDefinitionsApi

    client = context["get_config_client"]()
    api = DestinationDefinitionsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        ws = getattr(args, "workspace_id", None)
        result = api.list(workspace_id=ws)
        output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.definition_id)
        output(result, fmt)

    elif args.action == "create":
        payload = DestinationDefinitionCreate(
            name=args.name,
            docker_repository=args.docker_repository,
            docker_image_tag=args.docker_image_tag,
            documentation_url=args.documentation_url,
        )
        ws = getattr(args, "workspace_id", None)
        result = api.create(payload, workspace_id=ws)
        output(result, fmt)

    elif args.action == "update":
        payload = DestinationDefinitionCreate(
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
