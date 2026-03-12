"""API client for application endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse


class ApplicationsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, **params: Any) -> ApiResponse:
        resp = self.client.request("GET", "applications", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, application_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"applications/{application_id}")

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.client.request("POST", "applications", body=data)

    def delete(self, application_id: str) -> None:
        self.client.request("DELETE", f"applications/{application_id}")

    def token(self, application_id: str) -> dict[str, Any]:
        return self.client.request("POST", f"applications/{application_id}/token")
