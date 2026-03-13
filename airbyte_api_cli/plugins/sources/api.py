"""API client for source endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse

from .models import Source, SourceCreate


class SourcesApi:
    """Wraps the /sources Airbyte API endpoints."""

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
        resp = self.client.request("GET", "sources", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, source_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"sources/{source_id}")

    def create(self, data: SourceCreate) -> dict[str, Any]:
        return self.client.request("POST", "sources", body=data.to_dict())

    def update(self, source_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("PATCH", f"sources/{source_id}", body=data)

    def replace(self, source_id: str, data: SourceCreate) -> dict[str, Any]:
        return self.client.request("PUT", f"sources/{source_id}", body=data.to_dict())

    def delete(self, source_id: str) -> None:
        self.client.request("DELETE", f"sources/{source_id}")

    def oauth(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("POST", "sources/oauth", body=data)
