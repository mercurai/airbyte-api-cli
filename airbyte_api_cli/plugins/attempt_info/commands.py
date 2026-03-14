"""CLI commands for attempt_info."""
from __future__ import annotations
import argparse
from typing import Any
from airbyte_api_cli.core.output import error, output

def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("attempt_info", help="Job attempt details and debug info")
    sub = parser.add_subparsers(dest="action")

    get_cmd = sub.add_parser("get", help="Get attempt details for a job")
    get_cmd.add_argument("--job-id", required=True, type=int, dest="job_id")
    get_cmd.add_argument("--attempt", required=True, type=int, dest="attempt_number")

    debug_cmd = sub.add_parser("debug", help="Get debug info for a job")
    debug_cmd.add_argument("--job-id", required=True, type=int, dest="job_id")

    last_cmd = sub.add_parser("last-job", help="Get last replication job for a connection")
    last_cmd.add_argument("--connection-id", required=True, dest="connection_id")

    parser.set_defaults(handler=_handle)

def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import AttemptInfoApi
    client = context["get_config_client"]()
    api = AttemptInfoApi(client)
    fmt = context.get("format", "json")

    if args.action == "get":
        result = api.get_for_job(args.job_id, args.attempt_number)
        output(result, fmt)
    elif args.action == "debug":
        result = api.get_debug_info(args.job_id)
        output(result, fmt)
    elif args.action == "last-job":
        result = api.get_last_replication_job(args.connection_id)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
