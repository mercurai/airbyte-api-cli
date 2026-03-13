"""Data models for tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Tag:
    """Tag returned by the Airbyte API."""

    tag_id: str
    name: str
    color: str
    workspace_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tag:
        return cls(
            tag_id=data.get("tagId", ""),
            name=data.get("name", ""),
            color=data.get("color", ""),
            workspace_id=data.get("workspaceId", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tagId": self.tag_id,
            "name": self.name,
            "color": self.color,
            "workspaceId": self.workspace_id,
        }
