"""CLI commands for jobs."""

from __future__ import annotations

import argparse
from typing import Any

from airbyte_cli.core.output import error, output
from airbyte_cli.core.utils import strip_none


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `jobs` subcommand."""
    parser = subparsers.add_parser("jobs", help="Manage sync jobs")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List jobs")
    list_cmd.add_argument("--connection-id", dest="connection_id")
    list_cmd.add_argument("--workspace-id", dest="workspace_id")
    list_cmd.add_argument(
        "--status",
        choices=["pending", "running", "incomplete", "failed", "succeeded", "cancelled"],
    )
    list_cmd.add_argument(
        "--type",
        dest="job_type",
        choices=["sync", "reset", "refresh", "clear"],
    )
    list_cmd.add_argument(
        "--order-by",
        dest="order_by",
        choices=["createdAt", "updatedAt"],
    )
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    # trigger
    trigger_cmd = sub.add_parser("trigger", help="Trigger a job")
    trigger_cmd.add_argument("--connection-id", required=True, dest="connection_id")
    trigger_cmd.add_argument(
        "--type",
        required=True,
        dest="job_type",
        choices=["sync", "reset", "refresh", "clear"],
    )

    # get
    get_cmd = sub.add_parser("get", help="Get job details")
    get_cmd.add_argument("--id", required=True, dest="job_id")

    # cancel
    cancel_cmd = sub.add_parser("cancel", help="Cancel a job")
    cancel_cmd.add_argument("--id", required=True, dest="job_id")

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import JobsApi

    api = JobsApi(context["client"])
    fmt = context.get("format", "json")

    if args.action == "list":
        params = strip_none({
            "connectionId": getattr(args, "connection_id", None),
            "workspaceIds": getattr(args, "workspace_id", None),
            "status": getattr(args, "status", None),
            "jobType": getattr(args, "job_type", None),
            "orderBy": getattr(args, "order_by", None),
            "limit": args.limit,
            "offset": args.offset,
        })
        result = api.list(**params)
        output(result.data, fmt)

    elif args.action == "trigger":
        result = api.trigger(args.connection_id, args.job_type)
        output(result, fmt)

    elif args.action == "get":
        result = api.get(args.job_id)
        output(result, fmt)

    elif args.action == "cancel":
        api.cancel(args.job_id)

    else:
        error("usage", "No action specified. Use --help.")
        return 1

    return 0
