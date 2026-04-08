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
        # Guard against the Airbyte v1 PATCH /connections/{id} footgun: when
        # the body omits "status", the server silently resets it to "active".
        # See mercurai/airbyte-mercurai#7 for the March 20 zombie-sync incident.
        # Always GET the current connection and merge its status if the caller
        # didn't supply one. Callers can still force a status change by
        # including "status" explicitly.
        if "status" not in data:
            current = self.client.request("GET", f"connections/{connection_id}")
            current_status = current.get("status")
            if current_status:
                data = {**data, "status": current_status}
        return self.client.request("PATCH", f"connections/{connection_id}", body=data)

    def delete(self, connection_id: str) -> None:
        self.client.request("DELETE", f"connections/{connection_id}")
