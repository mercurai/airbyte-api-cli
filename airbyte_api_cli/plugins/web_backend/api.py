"""API client for web_backend endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse


class WebBackendApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list_connections(self, workspace_id: str) -> ApiResponse:
        resp = self.client.request(
            "POST", "web_backend/connections/list",
            body={"workspaceId": workspace_id},
        )
        return ApiResponse(data=resp.get("connections", []))

    def get_connection(self, connection_id: str, with_refreshed_catalog: bool = False) -> dict[str, Any]:
        return self.client.request(
            "POST", "web_backend/connections/get",
            body={"connectionId": connection_id, "withRefreshedCatalog": with_refreshed_catalog},
        )

    def check_updates(self) -> dict[str, Any]:
        return self.client.request("POST", "web_backend/check_updates", body={})

    def workspace_state(self, workspace_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "web_backend/workspace/state",
            body={"workspaceId": workspace_id},
        )
