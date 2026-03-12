"""Connections plugin — registers `connections` subcommand with the registry."""

from airbyte_cli.core.registry import Registry

from .commands import register_commands


def register() -> None:
    Registry.instance().register("connections", register_commands)


register()
