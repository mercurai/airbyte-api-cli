# Airbyte API CLI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool (stdlib only) for managing self-hosted Airbyte deployments via the REST API, plus Claude Code agent and skills.

**Architecture:** Plugin-based modular architecture. Core framework (HTTP client, auth, config, registry, output) + 15 resource plugins (sources, destinations, connections, jobs, etc.) + agent definition + 6 skills. Each plugin is self-contained with commands, API, and models.

**Tech Stack:** Python 3.10+ stdlib only (urllib.request, argparse, dataclasses, json, pathlib, unittest)

**Spec:** `docs/superpowers/specs/2026-03-12-airbyte-api-cli-design.md`

**Base directory:** `D:/projects/ticket-projects/seatiq/airbyte/airbyte-api-cli/`

---

## Chunk 1: Core Framework

All plugins depend on the core. Must be completed first.

### Task 1: Project Scaffolding + Shared Models

**Files:**
- Create: `airbyte_cli/__init__.py`
- Create: `airbyte_cli/__main__.py` (stub)
- Create: `airbyte_cli/core/__init__.py`
- Create: `airbyte_cli/core/exceptions.py`
- Create: `airbyte_cli/models/__init__.py`
- Create: `airbyte_cli/models/common.py`
- Create: `airbyte_cli/plugins/__init__.py` (stub)
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Create directory structure**

```bash
cd D:/projects/ticket-projects/seatiq/airbyte/airbyte-api-cli
mkdir -p airbyte_cli/core airbyte_cli/models airbyte_cli/plugins tests
```

- [ ] **Step 2: Create `airbyte_cli/__init__.py`**

```python
"""Airbyte API CLI — manage self-hosted Airbyte via the REST API."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create `airbyte_cli/core/exceptions.py`**

Custom exception hierarchy:

```python
"""Typed exceptions for the Airbyte CLI."""


class AirbyteCliError(Exception):
    """Base exception for all CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class ApiError(AirbyteCliError):
    """API returned an error response (4xx/5xx)."""

    def __init__(self, message: str, status_code: int, response_body: dict | None = None):
        super().__init__(message, exit_code=1)
        self.status_code = status_code
        self.response_body = response_body or {}


class AuthError(AirbyteCliError):
    """Authentication failed — invalid/expired credentials."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, exit_code=2)


class ConfigError(AirbyteCliError):
    """Missing or invalid configuration."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=3)


class NetworkError(AirbyteCliError):
    """Network connectivity issue — timeout, connection refused."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=4)
```

- [ ] **Step 4: Create `airbyte_cli/models/common.py`**

Shared dataclasses used by all plugins:

```python
"""Shared models used across all plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
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
```

- [ ] **Step 5: Create `airbyte_cli/models/__init__.py`**

```python
"""Data models for the Airbyte CLI."""

from airbyte_cli.models.common import ApiResponse, ErrorDetail

__all__ = ["ApiResponse", "ErrorDetail"]
```

- [ ] **Step 6: Create `airbyte_cli/core/__init__.py`**

```python
"""Core framework for the Airbyte CLI."""
```

- [ ] **Step 7: Create stub `airbyte_cli/__main__.py`**

```python
"""Entry point for python -m airbyte_cli."""

import sys


def main() -> int:
    """CLI entry point. Returns exit code."""
    print("airbyte-cli v0.1.0", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 8: Create stub `airbyte_cli/plugins/__init__.py`**

```python
"""Plugin auto-discovery. Imports all plugin packages to trigger registration."""
```

- [ ] **Step 9: Write tests for models**

```python
"""Tests for shared models."""

import unittest

from airbyte_cli.models.common import ApiResponse, ErrorDetail


class TestApiResponse(unittest.TestCase):
    def test_empty_response(self):
        resp = ApiResponse(data=[])
        self.assertEqual(resp.data, [])
        self.assertIsNone(resp.next_url)
        self.assertIsNone(resp.previous_url)

    def test_response_with_pagination(self):
        resp = ApiResponse(
            data=[{"id": "1"}],
            next_url="https://api.example.com/v1/sources?offset=20",
            previous_url=None,
        )
        self.assertEqual(len(resp.data), 1)
        self.assertIsNotNone(resp.next_url)


class TestErrorDetail(unittest.TestCase):
    def test_to_dict(self):
        err = ErrorDetail(error_type="not_found", message="Source not found", status=404)
        d = err.to_dict()
        self.assertEqual(d["error"], "not_found")
        self.assertEqual(d["status"], 404)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 10: Run tests**

Run: `cd D:/projects/ticket-projects/seatiq/airbyte/airbyte-api-cli && python -m pytest tests/ -v 2>/dev/null || python -m unittest discover -s tests -v`
Expected: All pass

- [ ] **Step 11: Commit**

```bash
git add -A && git commit -m "feat: project scaffolding, shared models, exception hierarchy"
```

---

### Task 2: Configuration Module

**Files:**
- Create: `airbyte_cli/core/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write tests for config**

```python
"""Tests for configuration module."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from airbyte_cli.core.config import Config


class TestConfigFromEnv(unittest.TestCase):
    @patch.dict(os.environ, {"AIRBYTE_BASE_URL": "https://test.example.com/api/public/v1"})
    def test_base_url_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.base_url, "https://test.example.com/api/public/v1")

    @patch.dict(os.environ, {"AIRBYTE_TOKEN": "tok_123"})
    def test_token_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.token, "tok_123")

    @patch.dict(os.environ, {
        "AIRBYTE_CLIENT_ID": "cid",
        "AIRBYTE_CLIENT_SECRET": "csec",
    })
    def test_client_credentials_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.client_id, "cid")
        self.assertEqual(cfg.client_secret, "csec")


class TestConfigFromFile(unittest.TestCase):
    def test_load_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({
                "base_url": "https://file.example.com/api/public/v1",
                "client_id": "file_cid",
                "client_secret": "file_csec",
                "default_workspace_id": "ws_123",
                "default_format": "table",
            }))
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "https://file.example.com/api/public/v1")
            self.assertEqual(cfg.default_workspace_id, "ws_123")
            self.assertEqual(cfg.default_format, "table")


class TestConfigPriority(unittest.TestCase):
    @patch.dict(os.environ, {"AIRBYTE_BASE_URL": "https://env.example.com/api/public/v1"})
    def test_env_overrides_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({"base_url": "https://file.example.com"}))
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "https://env.example.com/api/public/v1")

    def test_cli_overrides_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config.load(
                config_dir=Path(tmpdir),
                cli_overrides={"base_url": "https://cli.example.com"},
            )
            self.assertEqual(cfg.base_url, "https://cli.example.com")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement `airbyte_cli/core/config.py`**

```python
"""Configuration management with CLI > env > file priority."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "airbyte-cli"


@dataclass
class Config:
    """Resolved configuration from all sources."""

    base_url: str = ""
    token: str = ""
    client_id: str = ""
    client_secret: str = ""
    default_workspace_id: str = ""
    default_format: str = "json"
    timeout: int = 30

    @classmethod
    def load(
        cls,
        config_dir: Path | None = None,
        cli_overrides: dict[str, Any] | None = None,
    ) -> Config:
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
            "default_workspace_id": "AIRBYTE_WORKSPACE_ID",
        }
        env_vals = {}
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
            "default_workspace_id": self.default_workspace_id,
            "default_format": self.default_format,
        }
        # Don't persist token or secrets to file unnecessarily
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests/test_config.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add airbyte_cli/core/config.py tests/test_config.py
git commit -m "feat: configuration module with CLI > env > file priority"
```

---

### Task 3: HTTP Client

**Files:**
- Create: `airbyte_cli/core/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write tests for HTTP client**

Test request building, retry logic, error handling, and response parsing. Mock `urllib.request.urlopen`.

Key test cases:
- `test_get_request_builds_correct_url` — verifies URL construction with base_url + path + params
- `test_post_request_sends_json_body` — verifies Content-Type and body serialization
- `test_auth_header_injected` — verifies Bearer token in Authorization header
- `test_user_agent_set` — verifies User-Agent header
- `test_retry_on_server_error` — verifies 3 retries with backoff on 500
- `test_no_retry_on_client_error` — verifies no retry on 400/404
- `test_api_error_raised_on_4xx` — verifies ApiError with status and body
- `test_auth_error_raised_on_401` — verifies AuthError
- `test_network_error_on_timeout` — verifies NetworkError
- `test_response_json_parsed` — verifies JSON response deserialized

- [ ] **Step 2: Implement `airbyte_cli/core/client.py`**

urllib.request wrapper with:
- `HttpClient.__init__(self, base_url, token, timeout=30)`
- `HttpClient.request(self, method, path, body=None, params=None) -> dict`
- URL construction: `base_url.rstrip("/") + "/" + path.lstrip("/")`
- Query params: `urllib.parse.urlencode`
- Headers: Authorization, Content-Type, User-Agent, Accept
- JSON body serialization with `json.dumps().encode("utf-8")`
- Response parsing with `json.loads()`
- Retry: 3 attempts, backoff [1, 2, 4] seconds, only on 500+/network errors
- Exception mapping: 401→AuthError, 4xx→ApiError, 5xx→ApiError (after retries), URLError→NetworkError

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests/test_client.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add airbyte_cli/core/client.py tests/test_client.py
git commit -m "feat: HTTP client with retry, auth injection, error handling"
```

---

### Task 4: Auth Module

**Files:**
- Create: `airbyte_cli/core/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write tests for auth**

Key test cases:
- `test_acquire_token_posts_client_credentials` — verifies POST to /applications/token with grant_type
- `test_token_cached_to_file` — verifies token.json written with expires_at
- `test_cached_token_loaded_when_valid` — verifies cached token used without HTTP call
- `test_expired_token_triggers_refresh` — verifies new token acquired when expires_at passed
- `test_direct_token_skips_credentials_flow` — verifies --token/AIRBYTE_TOKEN bypasses auth
- `test_auth_error_on_invalid_credentials` — verifies AuthError raised on 401 from token endpoint

- [ ] **Step 2: Implement `airbyte_cli/core/auth.py`**

```python
"""Token acquisition, caching, and refresh for Airbyte API."""

class TokenManager:
    def __init__(self, config: Config, config_dir: Path | None = None): ...
    def get_token(self) -> str: ...
    def _load_cached_token(self) -> str | None: ...
    def _acquire_token(self) -> str: ...
    def _cache_token(self, access_token: str, expires_in: int) -> None: ...
    def refresh(self) -> str: ...
```

Token flow:
1. If `config.token` set → return directly (no caching)
2. Check `token.json` → if `expires_at > now + 60` → return cached token
3. POST `/applications/token` with `{client_id, client_secret, grant_type: "client_credentials"}`
4. Cache response to `token.json` as `{access_token, expires_at: now + expires_in}`
5. Return access_token

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests/test_auth.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add airbyte_cli/core/auth.py tests/test_auth.py
git commit -m "feat: token management with caching and auto-refresh"
```

---

### Task 5: Plugin Registry + Output + Utils

**Files:**
- Create: `airbyte_cli/core/registry.py`
- Create: `airbyte_cli/core/output.py`
- Create: `airbyte_cli/core/utils.py`
- Create: `tests/test_registry.py`
- Create: `tests/test_output.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write tests for registry**

Test plugin registration and command dispatch.

- [ ] **Step 2: Implement `airbyte_cli/core/registry.py`**

```python
"""Plugin registry — maps command names to handler functions."""

class Registry:
    _instance = None
    _plugins: dict[str, PluginInfo]

    @classmethod
    def instance(cls) -> Registry: ...
    def register(self, name: str, setup_fn) -> None: ...
    def get_plugin(self, name: str) -> PluginInfo | None: ...
    def all_plugins(self) -> dict[str, PluginInfo]: ...
```

- [ ] **Step 3: Write tests for output**

Test JSON, table, and compact formatters.

- [ ] **Step 4: Implement `airbyte_cli/core/output.py`**

```python
"""Output formatters — JSON (default), table, compact."""

def format_json(data: Any) -> str: ...
def format_table(data: list[dict], columns: list[str] | None = None) -> str: ...
def format_compact(data: list[dict], columns: list[str] | None = None) -> str: ...
def output(data: Any, fmt: str = "json", columns: list[str] | None = None) -> None: ...
def error(error_type: str, message: str, status: int = 0) -> None: ...
```

- [ ] **Step 5: Write tests for utils**

Test `resolve_json_arg` with inline JSON and @file.json.

- [ ] **Step 6: Implement `airbyte_cli/core/utils.py`**

```python
"""Shared utilities."""

import json
from pathlib import Path

def resolve_json_arg(value: str) -> dict:
    """Parse JSON from inline string or @filepath."""
    if value.startswith("@"):
        path = Path(value[1:])
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)
```

- [ ] **Step 7: Run all tests**

Run: `python -m unittest discover -s tests -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add airbyte_cli/core/registry.py airbyte_cli/core/output.py airbyte_cli/core/utils.py tests/test_registry.py tests/test_output.py tests/test_utils.py
git commit -m "feat: plugin registry, output formatters, shared utils"
```

---

### Task 6: Entry Point + Config Command

**Files:**
- Modify: `airbyte_cli/__main__.py`
- Modify: `airbyte_cli/plugins/__init__.py`
- Create: `airbyte_cli/plugins/config_cmd/__init__.py`
- Create: `airbyte_cli/plugins/config_cmd/commands.py`

- [ ] **Step 1: Implement full `__main__.py`**

Wire up argparse root parser with global flags (`--base-url`, `--token`, `--format`), load config, initialize client, discover plugins, dispatch to handler.

- [ ] **Step 2: Implement config command plugin**

`airbyte config set --base-url X --client-id Y --client-secret Z`
`airbyte config show`

- [ ] **Step 3: Implement plugin auto-discovery in `plugins/__init__.py`**

Import all plugin packages to trigger registration.

- [ ] **Step 4: Test end-to-end**

Run: `cd D:/projects/ticket-projects/seatiq/airbyte/airbyte-api-cli && python -m airbyte_cli --help`
Expected: Shows help with available commands

Run: `python -m airbyte_cli config show`
Expected: Shows current config (empty defaults)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: CLI entry point, config command, plugin auto-discovery"
```

---

## Chunk 2: CRUD Plugins (Parallel)

All plugins in this chunk follow the same pattern and can be implemented in parallel by separate agents. Each plugin has 4 files: `__init__.py`, `commands.py`, `api.py`, `models.py`.

### Plugin Template

Every CRUD plugin follows this structure. Agents implementing individual plugins should use this template and adapt for the specific resource.

**`plugins/<resource>/__init__.py`:**
```python
"""<Resource> plugin — registers commands with the CLI registry."""

from airbyte_cli.core.registry import Registry

from .commands import register_commands

def register():
    Registry.instance().register("<resource>", register_commands)

register()
```

**`plugins/<resource>/models.py`:**
```python
"""Data models for <resource>."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class <Resource>:
    """<Resource> returned by the API."""
    <resource>_id: str
    name: str
    # ... resource-specific fields

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> <Resource>:
        return cls(
            <resource>_id=data.get("<resource>Id", ""),
            name=data.get("name", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"<resource>Id": self.<resource>_id, "name": self.name}
```

**`plugins/<resource>/api.py`:**
```python
"""API client for <resource> endpoints."""

from __future__ import annotations
from typing import Any

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse


class <Resource>Api:
    def __init__(self, client: HttpClient):
        self.client = client

    def list(self, **params) -> ApiResponse:
        resp = self.client.request("GET", "<resource>s", params=params)
        return ApiResponse(
            data=resp.get("data", []),
            next_url=resp.get("next"),
            previous_url=resp.get("previous"),
        )

    def get(self, resource_id: str) -> dict:
        return self.client.request("GET", f"<resource>s/{resource_id}")

    def create(self, data: dict) -> dict:
        return self.client.request("POST", "<resource>s", body=data)

    def update(self, resource_id: str, data: dict) -> dict:
        return self.client.request("PATCH", f"<resource>s/{resource_id}", body=data)

    def delete(self, resource_id: str) -> None:
        self.client.request("DELETE", f"<resource>s/{resource_id}")
```

**`plugins/<resource>/commands.py`:**
```python
"""CLI commands for <resource>."""

from __future__ import annotations
import argparse
from typing import Any

from airbyte_cli.core.output import output, error
from airbyte_cli.core.utils import resolve_json_arg


def register_commands(subparsers: argparse._SubParsersAction, context: dict) -> None:
    parser = subparsers.add_parser("<resource>s", help="Manage <resource>s")
    sub = parser.add_subparsers(dest="action")

    # list
    list_cmd = sub.add_parser("list", help="List <resource>s")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    # get
    get_cmd = sub.add_parser("get", help="Get <resource> details")
    get_cmd.add_argument("--id", required=True, dest="resource_id")

    # create
    create_cmd = sub.add_parser("create", help="Create a <resource>")
    # ... resource-specific args

    # update
    update_cmd = sub.add_parser("update", help="Update a <resource>")
    update_cmd.add_argument("--id", required=True, dest="resource_id")
    update_cmd.add_argument("--data", required=True, help="JSON or @file.json")

    # delete
    delete_cmd = sub.add_parser("delete", help="Delete a <resource>")
    delete_cmd.add_argument("--id", required=True, dest="resource_id")

    parser.set_defaults(handler=lambda args, ctx: _handle(args, ctx))


def _handle(args: argparse.Namespace, context: dict) -> int:
    from .api import <Resource>Api
    api = <Resource>Api(context["client"])
    fmt = context.get("format", "json")

    if args.action == "list":
        result = api.list(limit=args.limit, offset=args.offset)
        output(result.data, fmt)
    elif args.action == "get":
        result = api.get(args.resource_id)
        output(result, fmt)
    elif args.action == "create":
        # ... build data dict from args
        result = api.create(data)
        output(result, fmt)
    elif args.action == "update":
        data = resolve_json_arg(args.data)
        result = api.update(args.resource_id, data)
        output(result, fmt)
    elif args.action == "delete":
        api.delete(args.resource_id)
    else:
        error("usage", "No action specified. Use --help.")
        return 1
    return 0
```

---

### Task 7: Sources Plugin

**Files:**
- Create: `airbyte_cli/plugins/sources/__init__.py`
- Create: `airbyte_cli/plugins/sources/models.py`
- Create: `airbyte_cli/plugins/sources/api.py`
- Create: `airbyte_cli/plugins/sources/commands.py`
- Create: `tests/test_plugins/test_sources.py`

Full CRUD + oauth. Uses PATCH for update, PUT for replace.

Fields: sourceId, name, sourceType, workspaceId, configuration
Create requires: name, workspaceId, sourceType, configuration
Extra commands: `replace` (PUT), `oauth` (POST /sources/oauth)

- [ ] **Step 1: Write tests** — test API call construction for all 7 operations
- [ ] **Step 2: Implement models.py** — Source, SourceCreate dataclasses
- [ ] **Step 3: Implement api.py** — SourcesApi with list/get/create/update/replace/delete/oauth
- [ ] **Step 4: Implement commands.py** — register all subcommands with proper args
- [ ] **Step 5: Implement __init__.py** — register plugin
- [ ] **Step 6: Add to plugins/__init__.py import list**
- [ ] **Step 7: Run tests, commit**

---

### Task 8: Destinations Plugin

Same as sources but without oauth. Uses PATCH for update, PUT for replace.

Fields: destinationId, name, destinationType, workspaceId, configuration
Create requires: name, workspaceId, destinationType, configuration
Commands: list, get, create, update, replace, delete

- [ ] Follow same steps as Task 7, adapted for destinations

---

### Task 9: Connections Plugin

Fields: connectionId, name, sourceId, destinationId, workspaceId, status, schedule, dataResidency, configurations, namespaceDefinition, namespaceFormat, prefix, nonBreakingSchemaUpdatesBehavior
Create requires: sourceId, destinationId
Optional: name, schedule (JSON: {scheduleType, cronExpression}), configurations (JSON: {streams: [...]}), dataResidency, namespaceDefinition, status
Uses PATCH for update. No PUT.

Special args for create:
- `--source-id` (required)
- `--destination-id` (required)
- `--name` (optional)
- `--schedule` (JSON or @file: `{"scheduleType": "cron", "cronExpression": "0 0 * * *"}`)
- `--streams` (JSON or @file: stream configuration)
- `--status` (choices: active, inactive, deprecated)
- `--namespace` (choices: source, destination, custom_format)

- [ ] Follow same steps as Task 7, adapted for connections

---

### Task 10: Jobs Plugin

Different pattern — not standard CRUD.

Endpoints:
- `GET /jobs` — list with filters (connectionId, status, jobType, workspaceIds, limit, offset, orderBy, date filters)
- `POST /jobs` — trigger (body: {connectionId, jobType: "sync"|"reset"})
- `GET /jobs/{jobId}` — get details
- `DELETE /jobs/{jobId}` — cancel

Commands: list, trigger, get, cancel

Special args for list:
- `--connection-id`
- `--status` (choices: pending, running, incomplete, failed, succeeded, cancelled)
- `--type` (choices: sync, reset)
- `--order-by` (choices: createdAt, updatedAt)
- `--limit`, `--offset`

Special args for trigger:
- `--connection-id` (required)
- `--type` (required, choices: sync, reset)

- [ ] Follow template but adapt for non-CRUD pattern

---

### Task 11: Workspaces Plugin

Full CRUD + oauth override.

Fields: workspaceId, name, dataResidency, notifications
Create requires: name
Optional: organizationId, notifications (JSON)
Extra: `PUT /workspaces/{id}/oauthCredentials` — args: --actorType, --name, --configuration

- [ ] Follow same steps as Task 7, adapted for workspaces + oauth

---

### Task 12: Streams Plugin (Read-Only)

Single endpoint: `GET /streams/{id}`
Minimal plugin — no models.py needed.

- [ ] Implement with just commands.py and api.py

---

### Task 13: Permissions Plugin

Full CRUD.

Fields: permissionId, permissionType, userId, workspaceId, organizationId
Create requires: permissionType, userId
List filters: userId, organizationId

- [ ] Follow same steps as Task 7

---

### Task 14: Organizations Plugin (Read-Only + OAuth)

Two endpoints:
- `GET /organizations` — list
- `PUT /organizations/{id}/oauthCredentials` — set OAuth override

- [ ] Implement minimal plugin

---

### Task 15: Users Plugin (Read-Only)

Single endpoint: `GET /users`
List filters: organizationId

- [ ] Implement minimal plugin

---

### Task 16: Source Definitions Plugin

CRUD using PUT for update (not PATCH).

Fields: definitionId, name, dockerRepository, dockerImageTag, etc.
Uses PUT/{id} for update (full replace).

- [ ] Follow template but use PUT for update method

---

### Task 17: Destination Definitions Plugin

Same pattern as source definitions.

- [ ] Follow template, same as Task 16

---

### Task 18: Declarative Source Definitions Plugin

Same pattern as source definitions.

- [ ] Follow template, same as Task 16

---

### Task 19: Tags Plugin

Standard CRUD with PATCH for update.

Fields: tagId, name
Create requires: name

- [ ] Follow standard CRUD template

---

### Task 20: Applications Plugin

CRUD + token generation.

Fields: applicationId, name, clientId, clientSecret, createdAt
Create requires: name
Extra: `POST /applications/{id}/token` — generates access token
No update endpoint.

Commands: list, get, create, delete, token

- [ ] Follow template + add token command

---

### Task 21: Health Plugin (Minimal)

Single endpoint: `GET /health`
No models needed. Just commands.py.

- [ ] Implement minimal: `commands.py` only, prints health status

---

## Chunk 3: Integration, Agent, and Skills

### Task 22: Wire All Plugins + Integration Test

**Files:**
- Modify: `airbyte_cli/plugins/__init__.py` — import all 15 plugins + config_cmd
- Modify: `airbyte_cli/__main__.py` — ensure proper error handling, exit codes
- Create: `tests/test_integration.py` — end-to-end CLI parsing tests

- [ ] **Step 1: Update plugins/__init__.py to import all plugins**

```python
"""Plugin auto-discovery."""

from airbyte_cli.plugins import (
    config_cmd,
    sources,
    destinations,
    connections,
    jobs,
    workspaces,
    streams,
    permissions,
    organizations,
    users,
    source_definitions,
    destination_definitions,
    declarative_source_definitions,
    tags,
    applications,
    health,
)
```

- [ ] **Step 2: Write integration tests**

Test full CLI flow: parse args → resolve config → build client → dispatch to plugin → format output. Mock HTTP layer.

- [ ] **Step 3: Test all commands respond to --help**

```bash
python -m airbyte_cli --help
python -m airbyte_cli sources --help
python -m airbyte_cli sources list --help
python -m airbyte_cli connections create --help
python -m airbyte_cli jobs trigger --help
```

- [ ] **Step 4: Run full test suite**

Run: `python -m unittest discover -s tests -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: wire all 15 plugins, integration tests"
```

---

### Task 23: Agent Definition

**Files:**
- Create: `agent/airbyte-manager.md`

The agent definition for Claude Code. Describes:
- What the agent does (manages Airbyte via CLI)
- Available tools (Bash for running CLI commands)
- Command reference (all commands with examples)
- Multi-step workflow patterns
- Error handling guidance

- [ ] **Step 1: Write agent/airbyte-manager.md**

Include:
- Agent name, description, trigger phrases
- Full command reference table
- Example workflows (create source, set up pipeline, check sync status)
- Troubleshooting patterns
- Configuration guidance (how to set base_url, credentials)

- [ ] **Step 2: Commit**

```bash
git add agent/airbyte-manager.md
git commit -m "feat: Claude Code agent definition for airbyte management"
```

---

### Task 24: Skills

**Files:**
- Create: `agent/skills/manage-sources.md`
- Create: `agent/skills/manage-destinations.md`
- Create: `agent/skills/manage-connections.md`
- Create: `agent/skills/sync-status.md`
- Create: `agent/skills/setup-connection.md`
- Create: `agent/skills/troubleshoot.md`

Each skill provides a structured workflow that the agent follows when triggered.

- [ ] **Step 1: Write manage-sources.md** — guides through source type selection, config building, creation
- [ ] **Step 2: Write manage-destinations.md** — same pattern for destinations
- [ ] **Step 3: Write manage-connections.md** — connect source to destination with schedule
- [ ] **Step 4: Write sync-status.md** — check jobs, show recent syncs, diagnose failures
- [ ] **Step 5: Write setup-connection.md** — end-to-end: source → destination → connection → sync
- [ ] **Step 6: Write troubleshoot.md** — health check, job history, error diagnosis
- [ ] **Step 7: Commit**

```bash
git add agent/skills/
git commit -m "feat: 6 Claude Code skills for airbyte management workflows"
```

---

### Task 25: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README with:**
  - Installation (just clone, no pip install needed)
  - Configuration (env vars, config file, CLI flags)
  - Quick start (configure, list sources, create connection)
  - Full command reference
  - Agent usage (how to install agent + skills)

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README with full command reference and agent setup"
```

---

## Execution Strategy

**Phase 1 (sequential):** Tasks 1-6 (Core Framework) — must be sequential, each builds on the previous.

**Phase 2 (parallel):** Tasks 7-21 (Plugins) — all 15 plugins can be implemented in parallel by separate agents. Each plugin is independent and follows the template.

**Phase 3 (sequential):** Tasks 22-25 (Integration + Agent + Skills) — depends on all plugins being complete.

**Recommended agent dispatch for Phase 2:**
- Agent A: Tasks 7-8 (sources + destinations — full CRUD, most complex)
- Agent B: Tasks 9-10 (connections + jobs — complex, non-standard patterns)
- Agent C: Tasks 11-13 (workspaces + streams + permissions)
- Agent D: Tasks 14-18 (organizations + users + 3 definition plugins — lighter, similar patterns)
- Agent E: Tasks 19-21 (tags + applications + health — lightest)
