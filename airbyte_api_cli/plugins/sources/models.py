"""Data models for sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Source:
    """Source returned by the API."""

    source_id: str
    name: str
    source_type: str
    workspace_id: str
    configuration: dict[str, Any]
    definition_id: str = ""
    created_at: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Source:
        return cls(
            source_id=data.get("sourceId", ""),
            name=data.get("name", ""),
            source_type=data.get("sourceType", ""),
            workspace_id=data.get("workspaceId", ""),
            configuration=data.get("configuration", {}),
            definition_id=data.get("definitionId", ""),
            created_at=data.get("createdAt", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceId": self.source_id,
            "name": self.name,
            "sourceType": self.source_type,
            "workspaceId": self.workspace_id,
            "configuration": self.configuration,
            "definitionId": self.definition_id,
            "createdAt": self.created_at,
        }


@dataclass
class SourceCreate:
    """Payload for creating a source."""

    name: str
    workspace_id: str
    source_type: str
    configuration: dict[str, Any]
    definition_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "workspaceId": self.workspace_id,
            "sourceType": self.source_type,
            "configuration": self.configuration,
        }
        if self.definition_id:
            d["definitionId"] = self.definition_id
        return d
