"""API client for job endpoints."""

from __future__ import annotations

from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse


class JobsApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list(self, **params: Any) -> ApiResponse:
        resp = self.client.request("GET", "jobs", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def trigger(self, connection_id: str, job_type: str) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "jobs",
            body={"connectionId": connection_id, "jobType": job_type},
        )

    def get(self, job_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"jobs/{job_id}")

    def cancel(self, job_id: str) -> None:
        self.client.request("DELETE", f"jobs/{job_id}")
