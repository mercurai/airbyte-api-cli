"""Data models for the permissions plugin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Permission:
    """Represents an Airbyte permission entry."""

    permissionId: str
    permissionType: str
    userId: str
    workspaceId: str | None = None
    organizationId: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Permission":
        return cls(
            permissionId=data["permissionId"],
            permissionType=data["permissionType"],
            userId=data["userId"],
            workspaceId=data.get("workspaceId"),
            organizationId=data.get("organizationId"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "permissionId": self.permissionId,
            "permissionType": self.permissionType,
            "userId": self.userId,
            "workspaceId": self.workspaceId,
            "organizationId": self.organizationId,
        }
