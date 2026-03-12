"""Data models for source definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SourceDefinitionCreate:
    """Payload for creating or replacing a source definition."""

    name: str
    docker_repository: str
    docker_image_tag: str
    documentation_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "dockerRepository": self.docker_repository,
            "dockerImageTag": self.docker_image_tag,
        }
        if self.documentation_url:
            d["documentationUrl"] = self.documentation_url
        return d
