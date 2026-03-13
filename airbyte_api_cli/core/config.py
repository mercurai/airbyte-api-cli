"""Configuration management with CLI > env > file priority."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "airbyte-api-cli"


@dataclass
class Config:
    """Resolved configuration from all sources."""

    base_url: str = ""
    token: str = ""
    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    password: str = ""
    default_workspace_id: str = ""
    default_format: str = "json"
    timeout: int = 30

    @classmethod
    def load(
        cls,
        config_dir: Path | None = None,
        cli_overrides: dict[str, Any] | None = None,
    ) -> "Config":
        """Load config with priority: cli_overrides > env vars > config file."""
        config_dir = config_dir or DEFAULT_CONFIG_DIR
        cli_overrides = cli_overrides or {}

        # Layer 1: File defaults
        file_vals = cls._load_file(config_dir / "config.json")

        # Layer 2: Environment variables
        env_map = {
            "base_url": "AIRBYTE_BASE_URL",
            "token": "AIRBYTE_TOKEN",
            "client_id": "AIRBYTE_CLIENT_ID",
            "client_secret": "AIRBYTE_CLIENT_SECRET",
            "username": "AIRBYTE_USERNAME",
            "password": "AIRBYTE_PASSWORD",
            "default_workspace_id": "AIRBYTE_WORKSPACE_ID",
        }
        env_vals: dict[str, Any] = {}
        for key, env_name in env_map.items():
            val = os.environ.get(env_name)
            if val:
                env_vals[key] = val

        # Merge: file < env < cli
        merged = {**file_vals, **env_vals, **cli_overrides}

        return cls(
            base_url=merged.get("base_url", ""),
            token=merged.get("token", ""),
            client_id=merged.get("client_id", ""),
            client_secret=merged.get("client_secret", ""),
            username=merged.get("username", ""),
            password=merged.get("password", ""),
            default_workspace_id=merged.get("default_workspace_id", ""),
            default_format=merged.get("default_format", "json"),
            timeout=int(merged.get("timeout", 30)),
        )

    @staticmethod
    def _load_file(path: Path) -> dict[str, Any]:
        """Load config from JSON file. Returns empty dict if file missing."""
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, config_dir: Path | None = None) -> None:
        """Save current config to file."""
        config_dir = config_dir or DEFAULT_CONFIG_DIR
        config_dir.mkdir(parents=True, exist_ok=True)
        path = config_dir / "config.json"
        data = {
            "base_url": self.base_url,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "default_workspace_id": self.default_workspace_id,
            "default_format": self.default_format,
            "timeout": self.timeout,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        """Return config as dict (omitting sensitive token value)."""
        return {
            "base_url": self.base_url,
            "client_id": self.client_id,
            "client_secret": "***" if self.client_secret else "",
            "username": self.username,
            "password": "***" if self.password else "",
            "default_workspace_id": self.default_workspace_id,
            "default_format": self.default_format,
            "timeout": self.timeout,
        }
