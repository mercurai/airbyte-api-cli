"""Data models for applications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Application:
    """Application returned by the Airbyte API."""

    application_id: str
    name: str
    client_id: str
    client_secret: str
    created_at: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Application:
        return cls(
            application_id=data.get("applicationId", ""),
            name=data.get("name", ""),
            client_id=data.get("clientId", ""),
            client_secret=data.get("clientSecret", ""),
            created_at=data.get("createdAt", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "applicationId": self.application_id,
            "name": self.name,
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "createdAt": self.created_at,
        }
