"""Sources plugin — registers commands with the CLI registry."""

from airbyte_api_cli.core.registry import Registry

from .commands import register_commands


def register() -> None:
    Registry.instance().register("sources", register_commands)


register()
