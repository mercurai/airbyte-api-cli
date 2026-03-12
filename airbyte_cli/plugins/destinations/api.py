"""API client for destination endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse

from .models import DestinationCreate


class DestinationsApi:
    """Wraps the /destinations Airbyte API endpoints."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(
        self,
        workspace_ids: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ApiResponse:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if workspace_ids:
            params["workspaceIds"] = ",".join(workspace_ids)
        resp = self.client.request("GET", "destinations", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, destination_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"destinations/{destination_id}")

    def create(self, data: DestinationCreate) -> dict[str, Any]:
        return self.client.request("POST", "destinations", body=data.to_dict())

    def update(self, destination_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("PATCH", f"destinations/{destination_id}", body=data)

    def replace(self, destination_id: str, data: DestinationCreate) -> dict[str, Any]:
        return self.client.request("PUT", f"destinations/{destination_id}", body=data.to_dict())

    def delete(self, destination_id: str) -> None:
        self.client.request("DELETE", f"destinations/{destination_id}")
