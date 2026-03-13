"""Data models for declarative source definitions (OSS internal API)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeclarativeSourceDefinitionCreate:
    """Payload for creating or updating a declarative source manifest.

    Maps to the OSS internal API schema:
    {
        "workspaceId": "...",
        "sourceDefinitionId": "...",
        "setAsActiveManifest": true,
        "declarativeManifest": {
            "manifest": { ... },
            "spec": { ... },
            "description": "...",
            "version": 0
        }
    }
    """

    workspace_id: str
    source_definition_id: str
    manifest: dict[str, Any] = field(default_factory=dict)
    spec: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: int = 0
    set_as_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        decl: dict[str, Any] = {
            "manifest": self.manifest,
            "spec": self.spec,
            "version": self.version,
        }
        if self.description:
            decl["description"] = self.description
        return {
            "workspaceId": self.workspace_id,
            "sourceDefinitionId": self.source_definition_id,
            "setAsActiveManifest": self.set_as_active,
            "declarativeManifest": decl,
        }
