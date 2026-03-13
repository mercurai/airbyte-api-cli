"""API client for connection endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse


class ConnectionsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, **params: Any) -> ApiResponse:
        resp = self.client.request("GET", "connections", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, connection_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"connections/{connection_id}")

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("POST", "connections", body=data)

    def update(self, connection_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("PATCH", f"connections/{connection_id}", body=data)

    def delete(self, connection_id: str) -> None:
        self.client.request("DELETE", f"connections/{connection_id}")
