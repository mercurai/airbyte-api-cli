"""API calls for the workspaces plugin."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.core.utils import strip_none


def list_workspaces(client: HttpClient) -> list[dict[str, Any]]:
    resp = client.request("GET", "/workspaces")
    return resp.get("data", [])


def get_workspace(client: HttpClient, workspace_id: str) -> dict[str, Any]:
    return client.request("GET", f"/workspaces/{workspace_id}")


def create_workspace(
    client: HttpClient,
    name: str,
    organization_id: str | None = None,
    data_residency: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name}
    if organization_id is not None:
        body["organizationId"] = organization_id
    if data_residency is not None:
        body["dataResidency"] = data_residency
    return client.request("POST", "/workspaces", body=body)


def update_workspace(
    client: HttpClient,
    workspace_id: str,
    name: str | None = None,
    data_residency: str | None = None,
    notifications: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    body = strip_none({
        "name": name,
        "dataResidency": data_residency,
        "notifications": notifications,
    })
    return client.request("PATCH", f"/workspaces/{workspace_id}", body=body)


def delete_workspace(client: HttpClient, workspace_id: str) -> dict[str, Any]:
    return client.request("DELETE", f"/workspaces/{workspace_id}")


def set_oauth_credentials(
    client: HttpClient,
    workspace_id: str,
    actor_type: str,
    name: str,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    body = {
        "actorType": actor_type,
        "name": name,
        "configuration": configuration,
    }
    return client.request("PUT", f"/workspaces/{workspace_id}/oauthCredentials", body=body)
