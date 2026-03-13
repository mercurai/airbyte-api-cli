"""API client for source definition endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse

from .models import SourceDefinitionCreate


class SourceDefinitionsApi:
    """Wraps the /source_definitions OSS config API endpoints.

    Uses the internal RPC-style POST API at /api/v1/ which is the only
    way to manage connector definitions on self-hosted Airbyte OSS.
    """

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, workspace_id: str | None = None) -> ApiResponse:
        if workspace_id:
            resp = self.client.request(
                "POST",
                "source_definitions/list_for_workspace",
                body={"workspaceId": workspace_id},
            )
        else:
            resp = self.client.request(
                "POST", "source_definitions/list", body={}
            )
        return ApiResponse(data=resp.get("sourceDefinitions", []))

    def get(self, definition_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "source_definitions/get",
            body={"sourceDefinitionId": definition_id},
        )

    def create(
        self, data: SourceDefinitionCreate, workspace_id: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"sourceDefinition": data.to_dict()}
        if workspace_id:
            body["workspaceId"] = workspace_id
        return self.client.request(
            "POST", "source_definitions/create_custom", body=body
        )

    def update(self, definition_id: str, data: SourceDefinitionCreate) -> dict[str, Any]:
        body = data.to_dict()
        body["sourceDefinitionId"] = definition_id
        return self.client.request(
            "POST", "source_definitions/update", body=body
        )

    def delete(self, definition_id: str) -> None:
        self.client.request(
            "POST",
            "source_definitions/delete",
            body={"sourceDefinitionId": definition_id},
        )
