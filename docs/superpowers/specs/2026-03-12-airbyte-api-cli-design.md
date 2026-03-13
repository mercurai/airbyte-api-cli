---
owner: seatiq
last-reviewed: 2026-03-12
stability: draft
---

# Airbyte API CLI — Design Specification

## Purpose

A Python CLI tool for managing self-hosted Airbyte deployments via the REST API, plus Claude Code agent definitions and skills for AI-driven Airbyte management. Uses only Python standard library — no external dependencies.

## Success Criteria

- Full coverage of Airbyte public API v1 (~60 endpoints across 15 resource types)
- Zero external dependencies — stdlib only (urllib, json, argparse, dataclasses, etc.)
- Agent-friendly output — JSON to stdout, status/errors to stderr
- Claude Code agent and skills that can fully manage Airbyte without human intervention
- Production ready — proper error handling, retries, auth token management, config persistence
- SOLID, DRY, SRP compliant — modular plugin architecture, small focused files

## Architecture

### Plugin-Based Modular Architecture

Each API resource is a self-contained plugin. A thin core framework provides the HTTP client, auth, config, and command registration. Plugins register themselves automatically.

```
airbyte-api-cli/
├── airbyte_api_cli/
│   ├── __main__.py                  # Entry: python -m airbyte_api_cli
│   ├── __init__.py
│   ├── core/                        # Framework (~5 files)
│   │   ├── __init__.py
│   │   ├── client.py                # HTTP client (urllib.request)
│   │   ├── auth.py                  # Token acquisition, caching, refresh
│   │   ├── config.py                # Config hierarchy: CLI > env > file
│   │   ├── registry.py              # Plugin registry + command routing
│   │   ├── output.py                # JSON/table/compact formatters
│   │   └── utils.py                 # resolve_json_arg, shared helpers
│   ├── plugins/                     # Resource plugins (15 dirs)
│   │   ├── __init__.py              # Auto-discovery of plugins
│   │   ├── sources/
│   │   │   ├── __init__.py          # Registers with registry
│   │   │   ├── commands.py          # argparse subcommands
│   │   │   ├── api.py               # API calls (list, get, create, update, delete, oauth)
│   │   │   └── models.py            # Source, SourceCreate dataclasses
│   │   ├── destinations/
│   │   │   └── ...                  # Same 4-file structure
│   │   ├── connections/
│   │   │   └── ...
│   │   ├── jobs/
│   │   │   └── ...
│   │   ├── workspaces/
│   │   │   └── ...
│   │   ├── streams/
│   │   │   └── ...                  # Read-only: get only
│   │   ├── permissions/
│   │   │   └── ...
│   │   ├── organizations/
│   │   │   └── ...                  # Read-only: list + oauth
│   │   ├── users/
│   │   │   └── ...                  # Read-only: list only
│   │   ├── source_definitions/
│   │   │   └── ...
│   │   ├── destination_definitions/
│   │   │   └── ...
│   │   ├── declarative_source_definitions/
│   │   │   └── ...
│   │   ├── tags/
│   │   │   └── ...
│   │   ├── applications/
│   │   │   └── ...
│   │   └── health/
│   │       ├── __init__.py
│   │       └── commands.py          # Minimal: single GET /health endpoint
│   └── models/                      # Shared models
│       ├── __init__.py
│       └── common.py                # Pagination, ErrorResponse, ApiResponse
├── tests/                           # unittest-based tests
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_auth.py
│   ├── test_config.py
│   └── test_plugins/
│       └── ...
├── agent/                           # Claude Code agent + skills
│   ├── airbyte-manager.md           # Agent definition
│   └── skills/
│       ├── manage-sources.md
│       ├── manage-destinations.md
│       ├── manage-connections.md
│       ├── sync-status.md
│       ├── setup-connection.md
│       └── troubleshoot.md
└── README.md
```

### Core Framework

#### client.py — HTTP Client

Thin wrapper around `urllib.request`:
- `request(method, path, body=None, params=None) -> ApiResponse`
- Constructs full URL from base_url + path
- Injects `Authorization: Bearer <token>` header
- Sets `Content-Type: application/json`
- Serializes request body, deserializes response
- Retry with exponential backoff (3 attempts, 1s/2s/4s)
- Timeout: 30s default, configurable
- Raises typed exceptions: `ApiError`, `AuthError`, `NetworkError`, `ConfigError`
- Sets `User-Agent: airbyte-api-cli/0.1.0` header on all requests

#### auth.py — Token Management

- Acquires token via `POST /applications/token` with body: `{"client_id": "...", "client_secret": "...", "grant_type": "client_credentials"}`
- Response: `{"access_token": "...", "expires_in": 3600}`
- Caches token to `~/.config/airbyte-api-cli/token.json` as: `{"access_token": "...", "expires_at": <unix_timestamp>}` where `expires_at = now + expires_in`
- On cache miss/expiry, reads `client_id`/`client_secret` from config module (not directly from disk)
- Auto-refreshes on 401 response (one retry, then fail)
- Supports direct token via `--token` flag or `AIRBYTE_TOKEN` env var (skips client_credentials flow)

#### config.py — Configuration

Priority (highest wins):
1. CLI flags (`--base-url`, `--token`, `--format`)
2. Environment variables (`AIRBYTE_BASE_URL`, `AIRBYTE_CLIENT_ID`, `AIRBYTE_CLIENT_SECRET`, `AIRBYTE_TOKEN`)
3. Config file (`~/.config/airbyte-api-cli/config.json`)

Config file schema:
```json
{
  "base_url": "https://airbyte.example.com/api/public/v1",
  "client_id": "...",
  "client_secret": "...",
  "default_workspace_id": "...",
  "default_format": "json"
}
```

Supports `airbyte config set` and `airbyte config show` commands.

#### registry.py — Plugin Registry

- `Registry` singleton holds command name → handler mappings
- Each plugin calls `registry.register(name, subcommands)` in its `__init__.py`
- `plugins/__init__.py` imports all plugin packages for auto-registration
- Router dispatches `sys.argv` to the correct plugin handler

#### output.py — Output Formatting

Three modes via `--format`:
- `json` (default) — full JSON, agent-friendly
- `table` — human-readable aligned columns
- `compact` — one-line-per-record, pipe-friendly

All output to stdout. Status messages and errors to stderr.

### Plugin Structure (example: sources)

#### plugins/sources/models.py

```python
@dataclass
class Source:
    source_id: str
    name: str
    source_type: str
    workspace_id: str
    configuration: dict

@dataclass
class SourceCreate:
    name: str
    workspace_id: str
    source_type: str
    configuration: dict
```

#### plugins/sources/api.py

```python
class SourcesApi:
    def __init__(self, client: HttpClient):
        self.client = client

    def list(self, workspace_ids=None, limit=20, offset=0) -> ApiResponse: ...
    def get(self, source_id: str) -> Source: ...
    def create(self, data: SourceCreate) -> Source: ...
    def update(self, source_id: str, data: dict) -> Source: ...
    def replace(self, source_id: str, data: SourceCreate) -> Source: ...
    def delete(self, source_id: str) -> None: ...
    def oauth(self, data: dict) -> dict: ...
```

#### plugins/sources/commands.py

```python
def register(subparsers, registry):
    parser = subparsers.add_parser("sources", help="Manage sources")
    sub = parser.add_subparsers(dest="action")

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--workspace-id", ...)
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)

    get_cmd = sub.add_parser("get")
    get_cmd.add_argument("--id", required=True)

    create_cmd = sub.add_parser("create")
    create_cmd.add_argument("--name", required=True)
    create_cmd.add_argument("--workspace-id", required=True)
    create_cmd.add_argument("--type", required=True)
    create_cmd.add_argument("--config", required=True, help="JSON string or @file.json")

    # ... update, delete, oauth
```

### API Coverage

All 15 resource types with full CRUD where the API supports it.

**Verb mapping:**
- `update` = PATCH (partial update) for sources, destinations, connections, workspaces, permissions, tags
- `replace` = PUT (full overwrite) for sources, destinations
- `update` = PUT (full overwrite) for source_definitions, destination_definitions, declarative_source_definitions (no PATCH available)
- `trigger` = POST /jobs with `--type sync|reset` (maps to `{connectionId, jobType}`)
- `cancel` = DELETE /jobs/{id}

**Pagination:** List commands return one page by default. Use `--limit` (1-100, default 20) and `--offset` to paginate. Response includes `next`/`previous` cursor URLs. Auto-pagination is out of scope for v0.1.

**JSON file arguments:** `--config` and `--data` flags accept inline JSON or `@path/to/file.json`. A shared `resolve_json_arg(value: str) -> dict` utility in `core/utils.py` handles this for all plugins.

| Resource | Endpoints | Commands |
|----------|-----------|----------|
| sources | GET, POST, GET/{id}, PATCH/{id}, PUT/{id}, DELETE/{id}, POST/oauth | list, get, create, update, replace, delete, oauth |
| destinations | GET, POST, GET/{id}, PATCH/{id}, PUT/{id}, DELETE/{id} | list, get, create, update, replace, delete |
| connections | GET, POST, GET/{id}, PATCH/{id}, DELETE/{id} | list, get, create, update, delete |
| jobs | GET, POST, GET/{id}, DELETE/{id} | list, get, trigger, cancel |
| workspaces | GET, POST, GET/{id}, PATCH/{id}, DELETE/{id}, PUT/{id}/oauth | list, get, create, update, delete, oauth |
| streams | GET/{id} | get |
| permissions | GET, POST, GET/{id}, PATCH/{id}, DELETE/{id} | list, get, create, update, delete |
| organizations | GET, PUT/{id}/oauth | list, oauth |
| users | GET | list |
| source_definitions | GET, POST, GET/{id}, PUT/{id}, DELETE/{id} | list, get, create, update, delete |
| destination_definitions | GET, POST, GET/{id}, PUT/{id}, DELETE/{id} | list, get, create, update, delete |
| declarative_source_definitions | GET, POST, GET/{id}, PUT/{id}, DELETE/{id} | list, get, create, update, delete |
| tags | GET, POST, GET/{id}, PATCH/{id}, DELETE/{id} | list, get, create, update, delete |
| applications | GET, POST, GET/{id}, DELETE/{id}, POST/{id}/token | list, get, create, delete, token |
| health | GET | check |

### Error Handling

Exit codes:
- 0 — success
- 1 — API error (4xx/5xx from Airbyte)
- 2 — authentication error (invalid/expired token)
- 3 — configuration error (missing base_url, etc.)
- 4 — network error (connection refused, timeout)

Error output format (to stderr):
```json
{"error": "type", "message": "details", "status": 404}
```

### Agent Definition

The `airbyte-manager` agent (at `~/.claude/agents/airbyte-manager.md`) will:
- Have access to all Bash commands (to invoke the CLI)
- Know the full command reference
- Understand Airbyte concepts (sources, destinations, connections, sync modes)
- Handle multi-step workflows (e.g., create source → create destination → create connection → trigger sync)

### Skills

| Skill | Trigger | What it does |
|-------|---------|-------------|
| manage-sources | "add source", "configure source" | Guide through source creation with type selection and config |
| manage-destinations | "add destination", "configure destination" | Guide through destination creation |
| manage-connections | "connect", "wire up", "create pipeline" | Create connection between existing source and destination |
| sync-status | "sync status", "job status", "check sync" | Check running/recent jobs, show success/failure details |
| setup-connection | "set up airbyte", "new airbyte pipeline", "full sync setup" | Full workflow: source → destination → connection → initial sync |
| troubleshoot | "sync failed", "why did", "debug sync" | Diagnose failed jobs, check health, suggest fixes |

### Testing Strategy

- `unittest` only (no pytest)
- Mock HTTP responses using `unittest.mock.patch` on `urllib.request.urlopen`
- Test each layer independently:
  - Core: client request building, auth token flow, config precedence
  - Plugins: command parsing, API call construction, model serialization
- Integration test script that runs against a live Airbyte instance (optional, not automated)

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| API changes breaking CLI | Pin to v1 API, version in user-agent header |
| Large configuration objects for connectors | Accept `--config @file.json` to read from file |
| Token expiry mid-operation | Auto-refresh on 401, cache token with expiry |
| urllib limitations vs requests | Thin wrapper handles all edge cases centrally |
| Plugin boilerplate repetition | Base classes in core reduce per-plugin code |

## Dependencies

**Runtime:** Python 3.10+ standard library only
- `urllib.request` — HTTP
- `json` — serialization
- `argparse` — CLI parsing
- `dataclasses` — models
- `pathlib` — file paths
- `logging` — structured logging
- `configparser` / `json` — config files
- `enum` — status types
- `typing` — type hints
- `unittest` — tests
- `unittest.mock` — test mocking
- `http.client` — HTTP status codes
- `base64` — auth encoding if needed

**No external packages required.**
