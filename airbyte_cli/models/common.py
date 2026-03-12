"""Shared models used across all plugins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiResponse:
    """Wrapper for paginated list responses."""

    data: list[dict[str, Any]]
    next_url: str | None = None
    previous_url: str | None = None


@dataclass
class ErrorDetail:
    """Structured error from the API."""

    error_type: str
    message: str
    status: int

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.error_type, "message": self.message, "status": self.status}
