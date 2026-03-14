"""Data models for builder projects (OSS internal API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BuilderProjectPublish:
    """Payload for publishing a builder project as a source definition."""

    workspace_id: str
    project_id: str
    name: str
    manifest: dict
    spec: dict
    description: str = ""
    version: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspaceId": self.workspace_id,
            "builderProjectId": self.project_id,
            "name": self.name,
            "initialDeclarativeManifest": {
                "manifest": self.manifest,
                "spec": self.spec,
                "version": self.version,
                "description": self.description,
            },
        }


@dataclass
class BuilderProjectReadStream:
    """Payload for reading a stream from a builder project manifest."""

    workspace_id: str
    manifest: dict
    stream_name: str
    config: dict
    project_id: str = ""
    record_limit: int | None = None
    page_limit: int | None = None
    form_generated_manifest: bool = False

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "workspaceId": self.workspace_id,
            "manifest": self.manifest,
            "streamName": self.stream_name,
            "config": self.config,
            "formGeneratedManifest": self.form_generated_manifest,
        }
        if self.project_id:
            d["builderProjectId"] = self.project_id
        if self.record_limit is not None:
            d["recordLimit"] = self.record_limit
        if self.page_limit is not None:
            d["pageLimit"] = self.page_limit
        return d
