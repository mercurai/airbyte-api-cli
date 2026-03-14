"""API client for builder project endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse

from .models import BuilderProjectPublish, BuilderProjectReadStream


class BuilderProjectsApi:
    """Wraps the /connector_builder_projects OSS config API endpoints.

    Uses the internal RPC-style POST API at /api/v1/ which is the only
    way to manage builder projects on self-hosted Airbyte OSS.
    """

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, workspace_id: str) -> ApiResponse:
        resp = self.client.request(
            "POST",
            "connector_builder_projects/list",
            body={"workspaceId": workspace_id},
        )
        return ApiResponse(data=resp.get("projects", []))

    def get(self, workspace_id: str, project_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "connector_builder_projects/get_with_manifest",
            body={"workspaceId": workspace_id, "builderProjectId": project_id},
        )

    def create(self, workspace_id: str, name: str, manifest: dict) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "connector_builder_projects/create",
            body={
                "workspaceId": workspace_id,
                "builderProject": {"name": name, "draftManifest": manifest},
            },
        )

    def update(
        self, workspace_id: str, project_id: str, name: str, manifest: dict
    ) -> None:
        self.client.request(
            "POST",
            "connector_builder_projects/update",
            body={
                "workspaceId": workspace_id,
                "builderProjectId": project_id,
                "builderProject": {"name": name, "draftManifest": manifest},
            },
        )

    def delete(self, workspace_id: str, project_id: str) -> None:
        self.client.request(
            "POST",
            "connector_builder_projects/delete",
            body={"workspaceId": workspace_id, "builderProjectId": project_id},
        )

    def publish(self, data: BuilderProjectPublish) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "connector_builder_projects/publish",
            body=data.to_dict(),
        )

    def read_stream(self, data: BuilderProjectReadStream) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "connector_builder_projects/read_stream",
            body=data.to_dict(),
        )
