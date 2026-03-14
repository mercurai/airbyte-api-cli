"""API client for attempt and job debug endpoints (OSS internal API)."""
from __future__ import annotations
from typing import Any
from airbyte_api_cli.core.client import HttpClient

class AttemptInfoApi:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def get_for_job(self, job_id: int, attempt_number: int) -> dict[str, Any]:
        return self.client.request(
            "POST", "attempt/get_for_job",
            body={"jobId": job_id, "attemptNumber": attempt_number},
        )

    def get_debug_info(self, job_id: int) -> dict[str, Any]:
        return self.client.request(
            "POST", "jobs/get_debug_info",
            body={"id": job_id},
        )

    def get_last_replication_job(self, connection_id: str) -> dict[str, Any]:
        return self.client.request(
            "POST", "jobs/get_last_replication_job",
            body={"connectionId": connection_id},
        )
