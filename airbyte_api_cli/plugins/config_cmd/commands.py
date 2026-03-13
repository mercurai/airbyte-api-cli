"""CLI commands for configuration management."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from airbyte_api_cli.core.output import error, format_json


def register_commands(
    subparsers: argparse._SubParsersAction,
    context: dict[str, Any],
) -> None:
    """Register the `config` subcommand."""
    parser = subparsers.add_parser("config", help="Manage CLI configuration")
    sub = parser.add_subparsers(dest="config_action")

    # config show
    sub.add_parser("show", help="Show current configuration")

    # config set
    set_cmd = sub.add_parser("set", help="Set configuration values")
    set_cmd.add_argument("--base-url", dest="base_url", help="Airbyte API base URL")
    set_cmd.add_argument("--client-id", dest="client_id", help="OAuth client ID")
    set_cmd.add_argument("--client-secret", dest="client_secret", help="OAuth client secret")
    set_cmd.add_argument("--username", dest="username", help="Basic auth username")
    set_cmd.add_argument("--password", dest="password", help="Basic auth password")
    set_cmd.add_argument(
        "--workspace-id", dest="default_workspace_id", help="Default workspace ID"
    )
    set_cmd.add_argument(
        "--format",
        dest="default_format",
        choices=["json", "table", "compact"],
        help="Default output format",
    )

    parser.set_defaults(handler=_handle)


def _handle(args: argparse.Namespace, context: dict[str, Any]) -> int:
    """Dispatch config subcommand."""
    cfg = context.get("config")
    config_dir = context.get("config_dir")

    if args.config_action == "show":
        if cfg is None:
            print(format_json({}))
        else:
            print(format_json(cfg.to_dict()))
        return 0

    if args.config_action == "set":
        if cfg is None:
            error("config", "No configuration loaded")
            return 3

        updates: dict[str, Any] = {}
        if args.base_url:
            updates["base_url"] = args.base_url
        if args.client_id:
            updates["client_id"] = args.client_id
        if args.client_secret:
            updates["client_secret"] = args.client_secret
        if getattr(args, "username", None):
            updates["username"] = args.username
        if getattr(args, "password", None):
            updates["password"] = args.password
        if args.default_workspace_id:
            updates["default_workspace_id"] = args.default_workspace_id
        if args.default_format:
            updates["default_format"] = args.default_format

        for key, val in updates.items():
            setattr(cfg, key, val)

        cfg.save(config_dir=config_dir)
        print(format_json({"message": "Configuration saved", "updated": list(updates.keys())}))
        return 0

    # No subcommand — show help
    error("usage", "No config action specified. Use `config show` or `config set`.")
    return 1
