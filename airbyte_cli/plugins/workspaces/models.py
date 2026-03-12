"""Data models for the workspaces plugin."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Workspace:
    """Represents an Airbyte workspace."""

    workspaceId: str
    name: str
    dataResidency: str | None = None
    notifications: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workspace":
        return cls(
            workspaceId=data["workspaceId"],
            name=data["name"],
            dataResidency=data.get("dataResidency"),
            notifications=data.get("notifications", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspaceId": self.workspaceId,
            "name": self.name,
            "dataResidency": self.dataResidency,
            "notifications": self.notifications,
        }


@dataclass
class OAuthCredentials:
    """OAuth credentials for a workspace actor."""

    actorType: str
    name: str
    configuration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "actorType": self.actorType,
            "name": self.name,
            "configuration": self.configuration,
        }
