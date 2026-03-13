"""API calls for the streams plugin."""

from __future__ import annotations

from typing import Any

from airbyte_api_cli.core.client import HttpClient


def get_stream(client: HttpClient, stream_id: str) -> dict[str, Any]:
    return client.request("GET", f"/streams/{stream_id}")
