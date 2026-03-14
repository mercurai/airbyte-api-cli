"""CLI commands for notifications."""
from __future__ import annotations
import argparse
from typing import Any
from airbyte_api_cli.core.output import error, output

def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    parser = subparsers.add_parser("notifications", help="Test notification configurations")
    sub = parser.add_subparsers(dest="action")

    try_cmd = sub.add_parser("try", help="Test a notification")
    try_cmd.add_argument("--type", required=True, dest="notification_type",
                         choices=["slack", "email"], help="Notification type")
    try_cmd.add_argument("--webhook", default=None, help="Slack webhook URL")

    parser.set_defaults(handler=_handle)

def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    from .api import NotificationsApi
    client = context["get_config_client"]()
    api = NotificationsApi(client)
    fmt = context.get("format", "json")

    if args.action == "try":
        if args.notification_type == "slack" and not args.webhook:
            error("usage", "--webhook is required for slack notifications.")
            return 1
        result = api.try_notification(args.notification_type, slack_webhook=args.webhook)
        output(result, fmt)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
