"""Plugin registry — maps command names to handler functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class PluginInfo:
    """Metadata about a registered plugin."""

    name: str
    setup_fn: Callable[..., Any]


class Registry:
    """Singleton registry of CLI plugins."""

    _instance: "Registry | None" = None

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}

    @classmethod
    def instance(cls) -> "Registry":
        """Return the singleton Registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton — used in tests."""
        cls._instance = None

    def register(self, name: str, setup_fn: Callable[..., Any]) -> None:
        """Register a plugin by name with its argparse setup function."""
        self._plugins[name] = PluginInfo(name=name, setup_fn=setup_fn)

    def get_plugin(self, name: str) -> PluginInfo | None:
        """Retrieve a plugin by name. Returns None if not found."""
        return self._plugins.get(name)

    def all_plugins(self) -> dict[str, PluginInfo]:
        """Return all registered plugins."""
        return dict(self._plugins)

    def setup_subparsers(self, subparsers: Any, context: dict[str, Any]) -> None:
        """Call setup_fn for every registered plugin."""
        for plugin in self._plugins.values():
            plugin.setup_fn(subparsers, context)
