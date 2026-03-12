"""API client for source definition endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse

from .models import SourceDefinitionCreate


class SourceDefinitionsApi:
    """Wraps the /source_definitions Airbyte API endpoints."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, limit: int = 20, offset: int = 0) -> ApiResponse:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        resp = self.client.request("GET", "source_definitions", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, definition_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"source_definitions/{definition_id}")

    def create(self, data: SourceDefinitionCreate) -> dict[str, Any]:
        return self.client.request("POST", "source_definitions", body=data.to_dict())

    def update(self, definition_id: str, data: SourceDefinitionCreate) -> dict[str, Any]:
        return self.client.request(
            "PUT", f"source_definitions/{definition_id}", body=data.to_dict()
        )

    def delete(self, definition_id: str) -> None:
        self.client.request("DELETE", f"source_definitions/{definition_id}")
