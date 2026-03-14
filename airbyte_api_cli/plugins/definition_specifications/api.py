"""API client for definition specification endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient


class DefinitionSpecificationsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def get_source_spec(self, source_definition_id: str, workspace_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "source_definition_specifications/get",
            body={"sourceDefinitionId": source_definition_id, "workspaceId": workspace_id},
        )

    def get_destination_spec(self, destination_definition_id: str, workspace_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "destination_definition_specifications/get",
            body={"destinationDefinitionId": destination_definition_id, "workspaceId": workspace_id},
        )
