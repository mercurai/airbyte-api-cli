"""API client for operations endpoints (OSS internal API)."""
from __future__ import annotations
from typing import Any
from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.models.common import ApiResponse

class OperationsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, connection_id: str) -> ApiResponse:
        resp = self.client.request(
            "POST", "operations/list",
            body={"connectionId": connection_id},
        )
        return ApiResponse(data=resp.get("operations", []))

    def get(self, operation_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "operations/get",
            body={"operationId": operation_id},
        )

    def create(self, connection_id: str, workspace_id: str, name: str, operator_config: dict) -> dict[str, Any]:
        return self.client.request(
            "POST", "operations/create",
            body={
                "connectionId": connection_id,
                "workspaceId": workspace_id,
                "name": name,
                "operatorConfiguration": operator_config,
            },
        )

    def update(self, operation_id: str, name: str, operator_config: dict) -> dict[str, Any]:
        return self.client.request(
            "POST", "operations/update",
            body={
                "operationId": operation_id,
                "name": name,
                "operatorConfiguration": operator_config,
            },
        )

    def delete(self, operation_id: str) -> None:
        self.client.request(
            "POST", "operations/delete",
            body={"operationId": operation_id},
        )

    def check(self, operator_config: dict) -> dict[str, Any]:
        return self.client.request(
            "POST", "operations/check",
            body={"operatorConfiguration": operator_config},
        )
