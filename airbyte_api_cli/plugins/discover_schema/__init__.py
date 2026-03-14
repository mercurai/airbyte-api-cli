"""Discover schema plugin — registers commands with the CLI registry."""
from airbyte_api_cli.core.registry import Registry
from .commands import register_commands

def register() -> None:
    Registry.instance().register("discover_schema", register_commands)

register()
