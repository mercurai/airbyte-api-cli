"""Data models for connections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Connection:
    """Connection returned by the Airbyte API."""

    connection_id: str
    name: str
    source_id: str
    destination_id: str
    workspace_id: str
    status: str
    data_residency: str
    namespace_definition: str
    namespace_format: str
    prefix: str
    non_breaking_schema_updates_behavior: str
    schedule: dict[str, Any] = field(default_factory=dict)
    configurations: dict[str, Any] = field(default_factory=dict)
    created_at: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Connection:
        return cls(
            connection_id=data.get("connectionId", ""),
            name=data.get("name", ""),
            source_id=data.get("sourceId", ""),
            destination_id=data.get("destinationId", ""),
            workspace_id=data.get("workspaceId", ""),
            status=data.get("status", ""),
            data_residency=data.get("dataResidency", ""),
            namespace_definition=data.get("namespaceDefinition", ""),
            namespace_format=data.get("namespaceFormat", ""),
            prefix=data.get("prefix", ""),
            non_breaking_schema_updates_behavior=data.get(
                "nonBreakingSchemaUpdatesBehavior", ""
            ),
            schedule=data.get("schedule", {}),
            configurations=data.get("configurations", {}),
            created_at=data.get("createdAt", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "connectionId": self.connection_id,
            "name": self.name,
            "sourceId": self.source_id,
            "destinationId": self.destination_id,
            "workspaceId": self.workspace_id,
            "status": self.status,
            "dataResidency": self.data_residency,
            "namespaceDefinition": self.namespace_definition,
            "namespaceFormat": self.namespace_format,
            "prefix": self.prefix,
            "nonBreakingSchemaUpdatesBehavior": self.non_breaking_schema_updates_behavior,
            "schedule": self.schedule,
            "configurations": self.configurations,
            "createdAt": self.created_at,
        }
