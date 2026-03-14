"""API client for state management endpoints (OSS internal API)."""
from __future__ import annotations
from typing import Any
from airbyte_api_cli.core.client import HttpClient

class StateApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def get(self, connection_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "state/get",
            body={"connectionId": connection_id},
        )

    def create_or_update(self, connection_id: str, connection_state: dict) -> dict[str, Any]:
        return self.client.request(
            "POST", "state/create_or_update",
            body={"connectionId": connection_id, "connectionState": connection_state},
        )
