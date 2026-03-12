"""API client for declarative source definition endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse

from .models import DeclarativeSourceDefinitionCreate


class DeclarativeSourceDefinitionsApi:
    """Wraps the /declarative_source_definitions OSS config API endpoints.

    Uses the internal RPC-style POST API at /api/v1/.  On OSS, declarative
    manifests are attached to an existing source definition (created first
    via source_definitions/create_custom with the airbyte/source-declarative-manifest
    Docker image).
    """

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list_manifests(
        self, workspace_id: str, source_definition_id: str
    ) -> ApiResponse:
        resp = self.client.request(
            "POST",
            "declarative_source_definitions/list_manifests",
            body={
                "workspaceId": workspace_id,
                "sourceDefinitionId": source_definition_id,
            },
        )
        return ApiResponse(data=resp.get("manifestVersions", []))

    def create_manifest(
        self, data: DeclarativeSourceDefinitionCreate
    ) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "declarative_source_definitions/create_manifest",
            body=data.to_dict(),
        )

    def update_manifest(
        self, data: DeclarativeSourceDefinitionCreate
    ) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "declarative_source_definitions/update_active_manifest",
            body=data.to_dict(),
        )
