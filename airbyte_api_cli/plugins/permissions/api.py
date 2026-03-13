"""API calls for the permissions plugin."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.core.utils import strip_none


def list_permissions(
    client: HttpClient,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> list[dict[str, Any]]:
    params = strip_none({"userId": user_id, "organizationId": organization_id})
    resp = client.request("GET", "/permissions", params=params or None)
    return resp.get("data", [])


def get_permission(client: HttpClient, permission_id: str) -> dict[str, Any]:
    return client.request("GET", f"/permissions/{permission_id}")


def create_permission(
    client: HttpClient,
    permission_type: str,
    user_id: str,
    workspace_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "permissionType": permission_type,
        "userId": user_id,
    }
    if workspace_id is not None:
        body["workspaceId"] = workspace_id
    if organization_id is not None:
        body["organizationId"] = organization_id
    return client.request("POST", "/permissions", body=body)


def update_permission(
    client: HttpClient,
    permission_id: str,
    permission_type: str | None = None,
) -> dict[str, Any]:
    body = strip_none({"permissionType": permission_type})
    return client.request("PATCH", f"/permissions/{permission_id}", body=body)


def delete_permission(client: HttpClient, permission_id: str) -> dict[str, Any]:
    return client.request("DELETE", f"/permissions/{permission_id}")
