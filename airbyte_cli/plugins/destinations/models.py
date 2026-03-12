"""Data models for destinations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Destination:
    """Destination returned by the API."""

    destination_id: str
    name: str
    destination_type: str
    workspace_id: str
    configuration: dict[str, Any]
    definition_id: str = ""
    created_at: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Destination:
        return cls(
            destination_id=data.get("destinationId", ""),
            name=data.get("name", ""),
            destination_type=data.get("destinationType", ""),
            workspace_id=data.get("workspaceId", ""),
            configuration=data.get("configuration", {}),
            definition_id=data.get("definitionId", ""),
            created_at=data.get("createdAt", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "destinationId": self.destination_id,
            "name": self.name,
            "destinationType": self.destination_type,
            "workspaceId": self.workspace_id,
            "configuration": self.configuration,
            "definitionId": self.definition_id,
            "createdAt": self.created_at,
        }


@dataclass
class DestinationCreate:
    """Payload for creating a destination."""

    name: str
    workspace_id: str
    destination_type: str
    configuration: dict[str, Any]
    definition_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "workspaceId": self.workspace_id,
            "destinationType": self.destination_type,
            "configuration": self.configuration,
        }
        if self.definition_id:
            d["definitionId"] = self.definition_id
        return d
