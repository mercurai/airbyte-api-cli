"""API client for discover_schema endpoint (OSS internal API)."""
from __future__ import annotations
from typing import Any
from airbyte_api_cli.core.client import HttpClient

class DiscoverSchemaApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def discover(self, source_id: str, disable_cache: bool = False) -> dict[str, Any]:
        body: dict[str, Any] = {"sourceId": source_id}
        if disable_cache:
            body["disable_cache"] = True
        return self.client.request("POST", "sources/discover_schema", body=body)
