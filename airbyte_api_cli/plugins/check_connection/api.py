"""API client for check_connection endpoints (OSS internal API)."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient


class CheckConnectionApi:
    """Wraps the check_connection OSS config API endpoints."""

    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def check_source(self, source_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "sources/check_connection",
            body={"sourceId": source_id},
        )

    def check_destination(self, destination_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "destinations/check_connection",
            body={"destinationId": destination_id},
        )
