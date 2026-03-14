"""CLI commands for builder projects."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_api_cli.core.output import error, output
from airbyte_api_cli.core.utils import resolve_json_arg

from .models import BuilderProjectPublish, BuilderProjectReadStream


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `builder_projects` subcommand tree."""
    parser = subparsers.add_parser("builder_projects", help="Manage connector builder projects")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List builder projects")
    list_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")

    # get
    get_cmd = sub.add_parser("get", help="Get a builder project with its manifest")
    get_cmd.add_argument("--id", required=True, dest="project_id")
    get_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a builder project")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    create_cmd.add_argument(
        "--manifest", default="{}", help="JSON manifest string or @file.json"
    )

    # update
    update_cmd = sub.add_parser("update", help="Update a builder project")
    update_cmd.add_argument("--id", required=True, dest="project_id")
    update_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    update_cmd.add_argument("--name", default=None)
    update_cmd.add_argument(
        "--manifest", default=None, help="JSON manifest string or @file.json"
    )

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a builder project")
    delete_cmd.add_argument("--id", required=True, dest="project_id")
    delete_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")

    # publish
    publish_cmd = sub.add_parser("publish", help="Publish a builder project as a source definition")
    publish_cmd.add_argument("--id", required=True, dest="project_id")
    publish_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    publish_cmd.add_argument(
        "--manifest", required=True, help="JSON manifest string or @file.json"
    )
    publish_cmd.add_argument(
        "--spec", required=True, help="JSON spec string or @file.json"
    )
    publish_cmd.add_argument("--name", default=None)
    publish_cmd.add_argument("--description", default="")
    publish_cmd.add_argument("--version", type=int, default=0)

    # read-stream
    read_stream_cmd = sub.add_parser("read-stream", help="Read records from a builder project stream")
    read_stream_cmd.add_argument("--workspace-id", required=True, dest="workspace_id")
    read_stream_cmd.add_argument("--stream-name", required=True, dest="stream_name")
    read_stream_cmd.add_argument(
        "--config", required=True, help="JSON config string or @file.json"
    )
    read_stream_cmd.add_argument("--project-id", default="", dest="project_id")
    read_stream_cmd.add_argument(
        "--manifest", default=None, help="JSON manifest string or @file.json"
    )
    read_stream_cmd.add_argument("--record-limit", type=int, default=None, dest="record_limit")
    read_stream_cmd.add_argument("--page-limit", type=int, default=None, dest="page_limit")
    read_stream_cmd.add_argument(
        "--form-generated-manifest",
        action="store_true",
        default=False,
        dest="form_generated_manifest",
    )

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch builder_projects subcommand."""
    from .api import BuilderProjectsApi

    client = context["get_config_client"]()
    api = BuilderProjectsApi(client)
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list(args.workspace_id)
        output(result.data, fmt)

    elif args.action == "get":
        result = api.get(args.workspace_id, args.project_id)
        output(result, fmt)

    elif args.action == "create":
        manifest = resolve_json_arg(args.manifest)
        result = api.create(args.workspace_id, args.name, manifest)
        output(result, fmt)

    elif args.action == "update":
        name = args.name
        manifest = resolve_json_arg(args.manifest) if args.manifest is not None else {}
        api.update(args.workspace_id, args.project_id, name, manifest)

    elif args.action == "delete":
        api.delete(args.workspace_id, args.project_id)

    elif args.action == "publish":
        manifest = resolve_json_arg(args.manifest)
        spec = resolve_json_arg(args.spec)
        name = args.name if args.name is not None else ""
        payload = BuilderProjectPublish(
            workspace_id=args.workspace_id,
            project_id=args.project_id,
            name=name,
            manifest=manifest,
            spec=spec,
            description=args.description,
            version=args.version,
        )
        result = api.publish(payload)
        output(result, fmt)

    elif args.action == "read-stream":
        manifest = None
        if args.manifest is not None:
            manifest = resolve_json_arg(args.manifest)
        elif args.project_id:
            project = api.get(args.workspace_id, args.project_id)
            manifest = project.get("manifest", {})
        else:
            error("usage", "Either --manifest or --project-id is required.")
            return 1

        config = resolve_json_arg(args.config)
        payload = BuilderProjectReadStream(
            workspace_id=args.workspace_id,
            manifest=manifest,
            stream_name=args.stream_name,
            config=config,
            project_id=args.project_id,
            record_limit=args.record_limit,
            page_limit=args.page_limit,
            form_generated_manifest=args.form_generated_manifest,
        )
        result = api.read_stream(payload)
        output(result, fmt)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
