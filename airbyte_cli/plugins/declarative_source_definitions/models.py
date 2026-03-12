"""Data models for declarative source definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeclarativeSourceDefinitionCreate:
    """Payload for creating or replacing a declarative source definition."""

    name: str
    workspace_id: str
    manifest: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "workspaceId": self.workspace_id,
            "declarativeManifest": {
                "manifest": self.manifest,
            },
        }
        if self.description:
            d["declarativeManifest"]["description"] = self.description
        return d
