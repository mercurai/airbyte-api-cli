"""Jobs plugin — registers `jobs` subcommand with the registry."""

from airbyte_cli.core.registry import Registry

from .commands import register_commands


def register() -> None:
    Registry.instance().register("jobs", register_commands)


register()
