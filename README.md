# Airbyte API CLI

A Python CLI for managing self-hosted Airbyte deployments via the [Airbyte REST API v1](https://reference.airbyte.com). Zero external dependencies — Python 3.10+ standard library only. No `pip install` needed.

Includes a [Claude Code](https://claude.ai/claude-code) agent definition and 6 skills for fully autonomous AI-driven Airbyte management.

## Features

- **Full API coverage** — 15 resource types, ~60 endpoints, every CRUD operation the Airbyte public API exposes
- **Zero dependencies** — stdlib only (`urllib.request`, `argparse`, `json`, `dataclasses`, `pathlib`)
- **Plugin architecture** — each resource is a self-contained package; adding a new one requires no core changes
- **Agent-friendly** — JSON to stdout, errors to stderr, deterministic exit codes
- **Flexible auth** — basic auth (username/password), OAuth2 client credentials, or direct bearer token
- **Three output modes** — `json` (default), `table` (human), `compact` (pipe-friendly)
- **Retry with backoff** — 3 retries on 5xx/network errors (1s, 2s, 4s delays)
- **Config hierarchy** — CLI flags > environment variables > config file

## Requirements

- Python 3.10 or later
- Network access to your Airbyte instance
- An Airbyte application (client_id + client_secret), a bearer token, or basic auth credentials (username + password)

## Installation

No installation required. Clone the repo and run directly:

```bash
git clone https://github.com/mercurai/airbyte-api-cli.git
cd airbyte-api-cli
python -m airbyte_api_cli --version
```

## Quick Start

### 1. Configure credentials

```bash
# Set your Airbyte API base URL
python -m airbyte_api_cli config set --base-url https://your-airbyte.example.com/api/public/v1

# Option A: Basic auth (common for self-hosted Airbyte OSS)
python -m airbyte_api_cli config set --username airbyte --password password

# Option B: Client credentials (recommended for Airbyte Cloud / automation)
python -m airbyte_api_cli config set --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET

# Option C: Direct bearer token
python -m airbyte_api_cli config set --token YOUR_BEARER_TOKEN
```

### 2. Verify connectivity

```bash
python -m airbyte_api_cli health
# {"available": true}
```

### 3. Explore your deployment

```bash
# List workspaces
python -m airbyte_api_cli workspaces list --format table

# List sources in a workspace
python -m airbyte_api_cli sources list --workspace-id <WS_ID>

# Get details for a specific source
python -m airbyte_api_cli sources get --id <SOURCE_ID>
```

### 4. Create a data pipeline

```bash
# Create a source
python -m airbyte_api_cli sources create \
  --name "Production Postgres" \
  --workspace-id <WS_ID> \
  --type postgres \
  --config @postgres-config.json

# Create a destination
python -m airbyte_api_cli destinations create \
  --name "Snowflake Warehouse" \
  --workspace-id <WS_ID> \
  --type snowflake \
  --config @snowflake-config.json

# Connect them
python -m airbyte_api_cli connections create \
  --source-id <SOURCE_ID> \
  --destination-id <DEST_ID> \
  --name "postgres-to-snowflake"

# Trigger the first sync
python -m airbyte_api_cli jobs trigger --connection-id <CONN_ID> --type sync
```

---

## Authentication

Four methods are supported, checked in this priority order:

### 1. Direct token (highest priority)

Pass a pre-obtained bearer token. Skips all other auth methods.

```bash
# Via CLI flag (per-invocation)
python -m airbyte_api_cli --token eyJhbGciOi... sources list

# Via environment variable
export AIRBYTE_TOKEN=eyJhbGciOi...
python -m airbyte_api_cli sources list

# Via config file
python -m airbyte_api_cli config set --token eyJhbGciOi...
```

### 2. Basic auth (common for self-hosted Airbyte OSS)

Username/password basic auth. The CLI sends a standard HTTP Basic `Authorization` header. This is the default auth method for self-hosted Airbyte OSS instances.

```bash
# Via CLI flags
python -m airbyte_api_cli --username airbyte --password password workspaces list

# Via environment variables
export AIRBYTE_USERNAME=airbyte
export AIRBYTE_PASSWORD=password

# Via config file
python -m airbyte_api_cli config set --username airbyte --password password
```

### 3. Client credentials (recommended for Airbyte Cloud / automation)

The CLI acquires a token via `POST /applications/token` using your application's client_id and client_secret. The token is cached to `~/.config/airbyte-api-cli/token.json` with its expiry timestamp. If the token expires (or a 401 is received), the CLI automatically refreshes it.

```bash
# Via environment variables
export AIRBYTE_CLIENT_ID=your_client_id
export AIRBYTE_CLIENT_SECRET=your_client_secret

# Or via config file
python -m airbyte_api_cli config set --client-id YOUR_ID --client-secret YOUR_SECRET
```

Token expiry varies by deployment: ~900 seconds on Airbyte Cloud, ~3600 seconds on self-managed. A 60-second buffer is applied — the CLI refreshes if less than 60 seconds remain.

### 4. Creating an application

If you don't have credentials yet, create an application through the CLI (requires an existing token or admin access):

```bash
python -m airbyte_api_cli applications create --name "my-cli-app"
# Returns: {"applicationId": "...", "name": "my-cli-app", "clientId": "...", "clientSecret": "..."}
```

Save the `clientId` and `clientSecret` from the response and configure them as above.

---

## Configuration

### Priority order (highest wins)

| Priority | Source | Example |
|----------|--------|---------|
| 1 | CLI flags | `--base-url`, `--token`, `--format` |
| 2 | Environment variables | `AIRBYTE_BASE_URL`, `AIRBYTE_TOKEN`, etc. |
| 3 | Config file | `~/.config/airbyte-api-cli/config.json` |

### Environment variables

| Variable | Purpose |
|----------|---------|
| `AIRBYTE_BASE_URL` | API base URL (e.g., `https://airbyte.example.com/api/public/v1`) |
| `AIRBYTE_TOKEN` | Bearer token (skips all other auth) |
| `AIRBYTE_USERNAME` | Basic auth username (for self-hosted Airbyte OSS) |
| `AIRBYTE_PASSWORD` | Basic auth password |
| `AIRBYTE_CLIENT_ID` | OAuth2 application client ID |
| `AIRBYTE_CLIENT_SECRET` | OAuth2 application client secret |
| `AIRBYTE_WORKSPACE_ID` | Default workspace ID for commands that accept `--workspace-id` |

### Config file

Located at `~/.config/airbyte-api-cli/config.json` by default (override with `--config-dir`):

```json
{
  "base_url": "https://airbyte.example.com/api/public/v1",
  "username": "airbyte",
  "password": "password",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "default_workspace_id": "ws_abc123",
  "default_format": "json"
}
```

### Managing config via CLI

```bash
# Show current config (secrets masked)
python -m airbyte_api_cli config show

# Set individual values
python -m airbyte_api_cli config set --base-url https://airbyte.example.com/api/public/v1
python -m airbyte_api_cli config set --username airbyte --password password
python -m airbyte_api_cli config set --client-id YOUR_ID --client-secret YOUR_SECRET
python -m airbyte_api_cli config set --workspace-id ws_abc123
python -m airbyte_api_cli config set --format table

# Use a custom config directory
python -m airbyte_api_cli --config-dir /path/to/config config show
```

---

## Global Flags

Available on every command:

```
--base-url URL      Airbyte API base URL (overrides config)
--token TOKEN       Bearer token (overrides config)
--username USER     Basic auth username (overrides config)
--password PASS     Basic auth password (overrides config)
--format FORMAT     Output format: json | table | compact (default: json)
--config-dir DIR    Config directory (default: ~/.config/airbyte-api-cli)
--version           Show version and exit
--help              Show help and exit
```

---

## Command Reference

### Health

```bash
python -m airbyte_api_cli health
```

Returns `{"available": true}` if the Airbyte API is reachable.

### Sources

Manage data sources (configured connector instances that read data).

```bash
# List all sources (optionally filtered by workspace)
python -m airbyte_api_cli sources list [--workspace-id WS_ID] [--limit 20] [--offset 0]

# Get source details
python -m airbyte_api_cli sources get --id <SOURCE_ID>

# Create a source
python -m airbyte_api_cli sources create \
  --name "My Postgres" \
  --workspace-id <WS_ID> \
  --type postgres \
  --config '{"host":"db.example.com","port":5432,"database":"mydb","username":"user","password":"pass"}' \
  [--definition-id <DEF_ID>]

# Partial update (PATCH) — only send changed fields
python -m airbyte_api_cli sources update --id <SOURCE_ID> --data '{"name":"New Name"}'

# Full replace (PUT) — must send all fields
python -m airbyte_api_cli sources replace --id <SOURCE_ID> \
  --name "My Postgres" --workspace-id <WS_ID> --type postgres --config @config.json

# Delete
python -m airbyte_api_cli sources delete --id <SOURCE_ID>

# Initiate OAuth flow
python -m airbyte_api_cli sources oauth --data '{"sourceType":"google-sheets","workspaceId":"..."}'
```

### Destinations

Manage data destinations (configured connector instances that write data).

```bash
python -m airbyte_api_cli destinations list [--workspace-id WS_ID] [--limit 20] [--offset 0]
python -m airbyte_api_cli destinations get --id <DEST_ID>
python -m airbyte_api_cli destinations create \
  --name "Snowflake" --workspace-id <WS_ID> --type snowflake --config @snowflake.json
python -m airbyte_api_cli destinations update --id <DEST_ID> --data '{"name":"New Name"}'
python -m airbyte_api_cli destinations replace --id <DEST_ID> \
  --name "Snowflake" --workspace-id <WS_ID> --type snowflake --config @snowflake.json
python -m airbyte_api_cli destinations delete --id <DEST_ID>
```

### Connections

Manage connections (links between a source and a destination with sync configuration).

```bash
# List connections
python -m airbyte_api_cli connections list [--workspace-id WS_ID] [--limit 20] [--offset 0]

# Get connection details
python -m airbyte_api_cli connections get --id <CONN_ID>

# Create a connection
python -m airbyte_api_cli connections create \
  --source-id <SOURCE_ID> \
  --destination-id <DEST_ID> \
  [--name "my-pipeline"] \
  [--status active|inactive|deprecated] \
  [--namespace source|destination|custom_format] \
  [--schedule '{"scheduleType":"cron","cronExpression":"0 0 * * *"}'] \
  [--streams '[{"name":"users","syncMode":"incremental_append"}]'] \
  [--data-residency auto|us|eu] \
  [--prefix "prod_"]

# Update a connection (PATCH)
python -m airbyte_api_cli connections update --id <CONN_ID> --data '{"status":"inactive"}'

# Delete
python -m airbyte_api_cli connections delete --id <CONN_ID>
```

### Jobs

Trigger and monitor sync operations.

```bash
# List jobs (with optional filters)
python -m airbyte_api_cli jobs list \
  [--connection-id CONN_ID] \
  [--workspace-id WS_ID] \
  [--status pending|running|incomplete|failed|succeeded|cancelled] \
  [--type sync|reset|refresh|clear] \
  [--order-by createdAt|updatedAt] \
  [--limit 20] [--offset 0]

# Get job details
python -m airbyte_api_cli jobs get --id <JOB_ID>

# Trigger a new job
python -m airbyte_api_cli jobs trigger --connection-id <CONN_ID> --type sync

# Cancel a running job
python -m airbyte_api_cli jobs cancel --id <JOB_ID>

# Wait for a job to complete (polls every 15s by default)
python -m airbyte_api_cli jobs wait --id <JOB_ID> [--interval 15] [--timeout 0]
```

`jobs wait` polls until the job reaches a terminal state (`succeeded`, `failed`, `cancelled`). Progress is printed to stderr; the final job JSON goes to stdout. Exit code 0 = succeeded, 1 = failed/cancelled/timeout.

**Job types:**

| Type | Description |
|------|-------------|
| `sync` | Run an incremental or full refresh sync per stream configuration |
| `reset` | Clear destination state and re-sync all data from scratch |
| `refresh` | Refresh source schema and re-sync |
| `clear` | Delete destination data without re-syncing |

### Workspaces

Manage workspaces (top-level organizational namespaces).

```bash
python -m airbyte_api_cli workspaces list
python -m airbyte_api_cli workspaces get --id <WS_ID>
python -m airbyte_api_cli workspaces create --name "Production" [--organization-id ORG_ID] [--data-residency us]
python -m airbyte_api_cli workspaces update --id <WS_ID> [--name "New Name"] [--data-residency eu]
python -m airbyte_api_cli workspaces delete --id <WS_ID>
python -m airbyte_api_cli workspaces oauth --id <WS_ID> --actor-type source --name "google" --config @oauth.json
```

### Streams

Inspect the stream catalog for a connection (read-only).

```bash
python -m airbyte_api_cli streams get --connection-id <CONN_ID>
```

Returns the list of available streams, their sync modes, and configuration.

### Permissions

Manage user permissions within workspaces and organizations.

```bash
python -m airbyte_api_cli permissions list [--limit 20] [--offset 0]
python -m airbyte_api_cli permissions get --id <PERM_ID>
python -m airbyte_api_cli permissions create --data '{"userId":"...","permissionType":"workspace_admin","workspaceId":"..."}'
python -m airbyte_api_cli permissions update --id <PERM_ID> --data '{"permissionType":"workspace_reader"}'
python -m airbyte_api_cli permissions delete --id <PERM_ID>
```

### Organizations

```bash
python -m airbyte_api_cli organizations list [--limit 20] [--offset 0]
python -m airbyte_api_cli organizations oauth --id <ORG_ID> --data '{"clientId":"...","clientSecret":"..."}'
```

### Users

```bash
python -m airbyte_api_cli users list --organization-id <ORG_ID> [--limit 20] [--offset 0]
```

### Source Definitions

Manage connector types available for creating sources (e.g., Postgres, Stripe, MySQL).
Uses the Airbyte internal config API (`/api/v1/`) — all operations are POST with JSON body.

```bash
python -m airbyte_api_cli source_definitions list [--workspace-id <WS_ID>]
python -m airbyte_api_cli source_definitions get --id <DEF_ID>
python -m airbyte_api_cli source_definitions create \
  --name "Custom Source" \
  --docker-repository my-org/source-custom \
  --docker-image-tag 1.0.0 \
  [--documentation-url https://docs.example.com] \
  [--workspace-id <WS_ID>]
python -m airbyte_api_cli source_definitions update --id <DEF_ID> \
  --name "Custom Source" --docker-repository my-org/source-custom --docker-image-tag 1.1.0
python -m airbyte_api_cli source_definitions delete --id <DEF_ID>
```

Without `--workspace-id`, `list` returns all definitions in the registry. With it, returns definitions available to that workspace.

### Destination Definitions

Manage connector types available for creating destinations. Same internal API pattern as source definitions.

```bash
python -m airbyte_api_cli destination_definitions list [--workspace-id <WS_ID>]
python -m airbyte_api_cli destination_definitions get --id <DEF_ID>
python -m airbyte_api_cli destination_definitions create \
  --name "Custom Dest" \
  --docker-repository my-org/dest-custom \
  --docker-image-tag 1.0.0 \
  [--documentation-url https://docs.example.com] \
  [--workspace-id <WS_ID>]
python -m airbyte_api_cli destination_definitions update --id <DEF_ID> \
  --name "Custom Dest" --docker-repository my-org/dest-custom --docker-image-tag 1.1.0
python -m airbyte_api_cli destination_definitions delete --id <DEF_ID>
```

### Declarative Source Definitions

Manage low-code connectors built with the [Airbyte CDK declarative framework](https://docs.airbyte.com/connector-development/config-based/). These are workspace-scoped manifests attached to an existing source definition (typically `airbyte/source-declarative-manifest`).

```bash
python -m airbyte_api_cli declarative_source_definitions list \
  --workspace-id <WS_ID> \
  --source-definition-id <DEF_ID>
python -m airbyte_api_cli declarative_source_definitions create \
  --workspace-id <WS_ID> \
  --source-definition-id <DEF_ID> \
  --manifest @manifest.json \
  [--spec @spec.json] \
  [--description "Reads from Example API"] \
  [--version 0]
python -m airbyte_api_cli declarative_source_definitions update \
  --workspace-id <WS_ID> \
  --source-definition-id <DEF_ID> \
  --manifest @manifest-v2.json \
  [--spec @spec.json] \
  [--version 1]
```

Both `--manifest` and `--spec` accept inline JSON strings or `@file.json` file references.

### Tags

Organize resources with workspace-scoped tags.

```bash
python -m airbyte_api_cli tags list [--workspace-id WS_ID] [--limit 20] [--offset 0]
python -m airbyte_api_cli tags get --id <TAG_ID>
python -m airbyte_api_cli tags create --name "production" --workspace-id <WS_ID> [--color "#FF0000"]
python -m airbyte_api_cli tags update --id <TAG_ID> [--name "staging"] [--color "#00FF00"]
python -m airbyte_api_cli tags delete --id <TAG_ID>
```

### Applications

Manage OAuth2 machine credentials for API access.

```bash
python -m airbyte_api_cli applications list [--limit 20] [--offset 0]
python -m airbyte_api_cli applications get --id <APP_ID>
python -m airbyte_api_cli applications create --name "ci-bot"
python -m airbyte_api_cli applications delete --id <APP_ID>
python -m airbyte_api_cli applications token --id <APP_ID>
```

`applications create` returns the `clientId` and `clientSecret` needed for authentication. `applications token` generates a short-lived access token for a specific application.

---

## Output Formats

Control output with `--format`:

### JSON (default)

Full JSON output, suitable for scripting and agent consumption:

```bash
python -m airbyte_api_cli sources list
```
```json
[
  {
    "sourceId": "abc123",
    "name": "Production Postgres",
    "sourceType": "postgres",
    "workspaceId": "ws_001"
  }
]
```

### Table

Human-readable aligned columns:

```bash
python -m airbyte_api_cli sources list --format table
```
```
SOURCEID  NAME                 SOURCETYPE  WORKSPACEID
--------  -------------------  ----------  -----------
abc123    Production Postgres  postgres    ws_001
def456    Staging MySQL        mysql       ws_001
```

### Compact

One line per record, pipe-delimited — ideal for `grep`, `awk`, `cut`:

```bash
python -m airbyte_api_cli sources list --format compact
```
```
abc123|Production Postgres|postgres|ws_001
def456|Staging MySQL|mysql|ws_001
```

---

## JSON File Arguments

Any flag that accepts JSON (`--config`, `--data`, `--manifest`, `--schedule`, `--streams`) supports two forms:

```bash
# Inline JSON string
python -m airbyte_api_cli sources create --config '{"host":"localhost","port":5432}'

# File reference (prefix with @)
python -m airbyte_api_cli sources create --config @path/to/config.json
```

File references are relative to the current working directory.

---

## Pagination

List commands return one page by default (20 records). Use `--limit` and `--offset` to paginate manually, or `--all` to fetch everything automatically:

```bash
# Single page
python -m airbyte_api_cli sources list --limit 50 --offset 0

# Fetch all records (auto-paginates)
python -m airbyte_api_cli sources list --all
```

`--all` is available on all list commands that support pagination (sources, destinations, connections, jobs, tags, applications, organizations, users). It fetches pages of `--limit` size (default 20) until all records are returned.

---

## Error Handling

### Exit codes

| Code | Type | Meaning |
|------|------|---------|
| `0` | Success | Command completed successfully |
| `1` | API error | Airbyte returned 4xx/5xx (check stderr for details) |
| `2` | Auth error | Invalid or expired credentials |
| `3` | Config error | Missing `base_url`, credentials, or invalid config |
| `4` | Network error | Connection refused, DNS failure, timeout |

### Error output format

Errors are written to stderr as JSON:

```json
{"error": "api", "message": "Source not found", "status": 404}
```

This allows scripts to parse errors separately from stdout data:

```bash
# Capture data and errors separately
python -m airbyte_api_cli sources get --id bad-id 2>error.json
```

### Retry behavior

The HTTP client automatically retries on:
- **5xx server errors** — 3 retries with exponential backoff (1s, 2s, 4s)
- **Network errors** (connection refused, timeout) — same retry policy

No retry on 4xx client errors or 401 auth errors.

---

## Architecture

```
airbyte-api-cli/
├── airbyte_api_cli/
│   ├── __main__.py              # CLI entry point (python -m airbyte_api_cli)
│   ├── __init__.py              # Package version
│   ├── core/                    # Framework layer
│   │   ├── client.py            # HTTP client (urllib.request + retry + auth)
│   │   ├── auth.py              # Token acquisition, caching, refresh
│   │   ├── config.py            # Config loading (CLI > env > file)
│   │   ├── registry.py          # Plugin registry + command routing
│   │   ├── output.py            # JSON/table/compact formatters
│   │   ├── utils.py             # resolve_json_arg, strip_none helpers
│   │   └── exceptions.py        # Typed exception hierarchy
│   ├── models/
│   │   └── common.py            # ApiResponse, ErrorDetail dataclasses
│   └── plugins/                 # Resource plugins (one package each)
│       ├── __init__.py           # Auto-discovery imports
│       ├── sources/             # __init__.py, commands.py, api.py, models.py
│       ├── destinations/
│       ├── connections/
│       ├── jobs/
│       ├── workspaces/
│       ├── streams/
│       ├── permissions/
│       ├── organizations/
│       ├── users/
│       ├── source_definitions/
│       ├── destination_definitions/
│       ├── declarative_source_definitions/
│       ├── tags/
│       ├── applications/
│       ├── health/
│       └── config_cmd/
├── tests/                       # 328 unit tests (unittest)
├── .claude/                     # Claude Code agent + skills
│   ├── agents/
│   │   └── airbyte-manager.md
│   └── skills/
│       ├── manage-sources/SKILL.md
│       ├── manage-destinations/SKILL.md
│       ├── manage-connections/SKILL.md
│       ├── sync-status/SKILL.md
│       ├── setup-connection/SKILL.md
│       └── troubleshoot/SKILL.md
└── README.md
```

### Plugin structure

Each resource plugin follows the same 4-file pattern:

| File | Responsibility |
|------|---------------|
| `__init__.py` | Imports `register_commands` and registers with the `Registry` singleton on import |
| `commands.py` | Defines argparse subcommands and the `_handle` dispatch function |
| `api.py` | API client class wrapping `HttpClient.request()` calls |
| `models.py` | Dataclasses for request/response payloads with `to_dict()`/`from_dict()` |

Simpler resources (health, streams, users, organizations) omit `models.py` when there's no structured payload.

### Adding a new plugin

1. Create `airbyte_api_cli/plugins/my_resource/` with `__init__.py`, `commands.py`, `api.py`, `models.py`
2. In `__init__.py`, call `Registry.instance().register("my_resource", register_commands)`
3. Add `from airbyte_api_cli.plugins import my_resource` to `plugins/__init__.py`
4. Create `tests/test_plugins/test_my_resource.py`

No changes to the core framework are needed.

---

## Claude Code Agent & Skills

The `.claude/` directory contains [Claude Code](https://claude.ai/claude-code) agent and skill definitions for autonomous Airbyte management. These follow the standard Claude Code directory layout and are automatically discovered by Claude Code.

### Agent: `airbyte-manager`

A Claude Code [subagent](https://code.claude.com/docs/en/sub-agents) (`.claude/agents/airbyte-manager.md`) that:
- Has full command reference for all 16 resources
- Understands Airbyte concepts (workspaces, sources, destinations, connections, streams, jobs)
- Executes multi-step workflows (pipeline setup, sync monitoring, troubleshooting)
- Uses Bash to invoke CLI commands and parse JSON output

### Skills

[Skills](https://code.claude.com/docs/en/skills) are in `.claude/skills/<name>/SKILL.md`. Invoke them with `/skill-name`.

| Skill | Slash command | Purpose |
|-------|--------------|---------|
| `manage-sources` | `/manage-sources` | Guide through source creation with type selection and config |
| `manage-destinations` | `/manage-destinations` | Guide through destination creation |
| `manage-connections` | `/manage-connections` | Wire a source to a destination with schedule and stream config |
| `sync-status` | `/sync-status` | Check running/recent jobs, show success/failure details |
| `setup-connection` | `/setup-connection` | End-to-end: source + destination + connection + initial sync |
| `troubleshoot` | `/troubleshoot` | Diagnose failures, inspect configs, suggest fixes |

---

## Testing

All tests use the Python standard library `unittest` module with `unittest.mock` for HTTP mocking. No test dependencies.

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run a specific test file
python -m unittest tests.test_client -v

# Run a specific plugin's tests
python -m unittest tests.test_plugins.test_sources -v

# Run a single test method
python -m unittest tests.test_plugins.test_sources.TestSourcesApi.test_list_returns_api_response -v
```

### Test coverage by layer

| Layer | Test files | What's tested |
|-------|-----------|---------------|
| Core | `test_client.py`, `test_auth.py`, `test_config.py`, `test_output.py`, `test_utils.py`, `test_registry.py`, `test_models.py` | HTTP request building, retry logic, auth token flow, config priority, formatters, JSON arg resolution |
| Plugins | `test_plugins/test_*.py` (15 files) | Command parsing, API call construction, model serialization, plugin registration |

---

## Common Workflows

### Monitor a sync to completion

```bash
# Trigger sync and wait for it to finish
JOB_JSON=$(python -m airbyte_api_cli jobs trigger --connection-id <CONN_ID> --type sync)
JOB_ID=$(echo "$JOB_JSON" | python -c "import sys,json; print(json.load(sys.stdin)['jobId'])")

# Wait for terminal state (polls every 15s, prints progress to stderr)
python -m airbyte_api_cli jobs wait --id "$JOB_ID"

# Or with custom interval and timeout
python -m airbyte_api_cli jobs wait --id "$JOB_ID" --interval 10 --timeout 3600
```

`jobs wait` exits with code 0 on success, 1 on failure/cancellation/timeout. The final job state is printed to stdout as JSON.

### Troubleshoot a failed sync

```bash
# 1. Check API health
python -m airbyte_api_cli health

# 2. Find the failed job
python -m airbyte_api_cli jobs list --connection-id <CONN_ID> --status failed --limit 5

# 3. Get failure details
python -m airbyte_api_cli jobs get --id <JOB_ID>

# 4. Inspect the connection and its source/destination
python -m airbyte_api_cli connections get --id <CONN_ID>
python -m airbyte_api_cli sources get --id <SOURCE_ID>
python -m airbyte_api_cli destinations get --id <DEST_ID>

# 5. After fixing the issue, re-trigger
python -m airbyte_api_cli jobs trigger --connection-id <CONN_ID> --type sync
```

### Bulk export all sources as JSON

```bash
python -m airbyte_api_cli sources list --limit 100 > sources.json
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
