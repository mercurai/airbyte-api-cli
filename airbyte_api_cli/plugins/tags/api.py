"""API client for tag endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse


class TagsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, **params: Any) -> ApiResponse:
        resp = self.client.request("GET", "tags", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, tag_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"tags/{tag_id}")

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("POST", "tags", body=data)

    def update(self, tag_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("PATCH", f"tags/{tag_id}", body=data)

    def delete(self, tag_id: str) -> None:
        self.client.request("DELETE", f"tags/{tag_id}")
