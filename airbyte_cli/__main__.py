"""Entry point for `python -m airbyte_cli`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from airbyte_cli import __version__
from airbyte_cli.core.config import Config, DEFAULT_CONFIG_DIR
from airbyte_cli.core.exceptions import AirbyteCliError
from airbyte_cli.core.output import error
from airbyte_cli.core.registry import Registry


def build_parser() -> argparse.ArgumentParser:
    """Build the root argument parser with global flags only (no subparsers)."""
    parser = argparse.ArgumentParser(
        prog="airbyte",
        description="Airbyte API CLI — manage self-hosted Airbyte via the REST API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # We'll add help to the full parser
    )
    parser.add_argument("--base-url", dest="base_url", help="Airbyte API base URL")
    parser.add_argument("--token", dest="token", help="API bearer token")
    parser.add_argument(
        "--format",
        dest="format",
        choices=["json", "table", "compact"],
        default=None,
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--config-dir",
        dest="config_dir",
        default=None,
        help=f"Config directory (default: {DEFAULT_CONFIG_DIR})",
    )
    return parser


def _load_config(args: argparse.Namespace, config_dir: Path) -> Config:
    """Build Config from file/env/CLI overrides."""
    cli_overrides: dict = {}
    if getattr(args, "base_url", None):
        cli_overrides["base_url"] = args.base_url
    if getattr(args, "token", None):
        cli_overrides["token"] = args.token
    if getattr(args, "format", None):
        cli_overrides["default_format"] = args.format
    return Config.load(config_dir=config_dir, cli_overrides=cli_overrides)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    # Auto-discover plugins (triggers registration via side-effect imports)
    import airbyte_cli.plugins  # noqa: F401

    # Pre-parse global flags only (ignoring unrecognised args like the subcommand)
    pre_parser = build_parser()
    pre, _ = pre_parser.parse_known_args(argv)
    config_dir = Path(pre.config_dir) if pre.config_dir else DEFAULT_CONFIG_DIR
    config = _load_config(pre, config_dir)

    # Build context passed to all plugin handlers
    context: dict = {
        "config": config,
        "config_dir": config_dir,
        "format": config.default_format,
    }

    # Build the full parser with subcommands
    full_parser = argparse.ArgumentParser(
        prog="airbyte",
        description="Airbyte API CLI — manage self-hosted Airbyte via the REST API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    full_parser.add_argument(
        "--version", action="version", version=f"airbyte-cli {__version__}"
    )
    full_parser.add_argument("--base-url", dest="base_url", help="Airbyte API base URL")
    full_parser.add_argument("--token", dest="token", help="API bearer token")
    full_parser.add_argument(
        "--format",
        dest="format",
        choices=["json", "table", "compact"],
        default=None,
        help="Output format (default: json)",
    )
    full_parser.add_argument(
        "--config-dir",
        dest="config_dir",
        default=None,
        help=f"Config directory (default: {DEFAULT_CONFIG_DIR})",
    )

    subparsers = full_parser.add_subparsers(dest="command", metavar="<command>")
    registry = Registry.instance()
    registry.setup_subparsers(subparsers, context)

    # Full parse
    args = full_parser.parse_args(argv)

    if args.command is None:
        full_parser.print_help(sys.stderr)
        return 0

    # Update format from fully parsed args
    if getattr(args, "format", None):
        context["format"] = args.format

    # Lazy HTTP client builder — only invoked when a command needs it
    def get_client():
        from airbyte_cli.core.auth import TokenManager
        from airbyte_cli.core.client import HttpClient

        token_mgr = TokenManager(config, config_dir=config_dir)
        token = token_mgr.get_token()
        return HttpClient(
            base_url=config.base_url,
            token=token,
            timeout=config.timeout,
        )

    context["get_client"] = get_client

    # Dispatch to plugin handler
    handler = getattr(args, "handler", None)
    if handler is None:
        # Plugin registered but no subcommand chosen — print plugin help
        full_parser.parse_args([args.command, "--help"])
        return 0

    try:
        return handler(args, context) or 0
    except AirbyteCliError as exc:
        error("cli_error", str(exc))
        return exc.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
