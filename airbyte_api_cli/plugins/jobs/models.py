"""Data models for jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Job:
    """Job returned by the Airbyte API."""

    job_id: int
    status: str
    job_type: str
    start_time: str
    connection_id: str
    last_updated_at: str
    duration: str
    bytes_synced: int
    rows_synced: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        return cls(
            job_id=data.get("jobId", 0),
            status=data.get("status", ""),
            job_type=data.get("jobType", ""),
            start_time=data.get("startTime", ""),
            connection_id=data.get("connectionId", ""),
            last_updated_at=data.get("lastUpdatedAt", ""),
            duration=data.get("duration", ""),
            bytes_synced=data.get("bytesSynced", 0),
            rows_synced=data.get("rowsSynced", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "status": self.status,
            "jobType": self.job_type,
            "startTime": self.start_time,
            "connectionId": self.connection_id,
            "lastUpdatedAt": self.last_updated_at,
            "duration": self.duration,
            "bytesSynced": self.bytes_synced,
            "rowsSynced": self.rows_synced,
        }
