"""Permissions plugin — registers `permissions` subcommand with the registry."""

from airbyte_api_cli.core.registry import Registry

from .commands import register_commands


def register() -> None:
    Registry.instance().register("permissions", register_commands)


register()
