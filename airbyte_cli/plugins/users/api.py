"""API client for user endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse


class UsersApi:
    """Wraps the /users Airbyte API endpoints."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, organization_id: str, limit: int = 20, offset: int = 0) -> ApiResponse:
        params: dict[str, Any] = {
            "organizationId": organization_id,
            "limit": limit,
            "offset": offset,
        }
        resp = self.client.request("GET", "users", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )
