"""API client for organization endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse


class OrganizationsApi:
    """Wraps the /organizations Airbyte API endpoints."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, limit: int = 20, offset: int = 0) -> ApiResponse:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        resp = self.client.request("GET", "organizations", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def update_oauth_credentials(
        self, organization_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        return self.client.request(
            "PUT", f"organizations/{organization_id}/oauthCredentials", body=data
        )
