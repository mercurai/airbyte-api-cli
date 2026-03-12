---
owner: seatiq
last-reviewed: 2026-03-12
stability: stable
---

# Airbyte API CLI

## Overview

A Python CLI tool for managing self-hosted Airbyte deployments via the REST API v1.
Uses only the Python standard library — no external dependencies, no pip install needed.
Includes a Claude Code agent definition and skills for AI-driven Airbyte management.

## Requirements

Python 3.10+ (stdlib only)

## Quick Start

```bash
# Configure
python -m airbyte_cli config set --base-url https://your-airbyte.example.com/api/public/v1
python -m airbyte_cli config set --client-id YOUR_ID --client-secret YOUR_SECRET

# Or use environment variables
export AIRBYTE_BASE_URL=https://your-airbyte.example.com/api/public/v1
export AIRBYTE_CLIENT_ID=your_id
export AIRBYTE_CLIENT_SECRET=your_secret

# Or pass a token directly
python -m airbyte_cli --token YOUR_TOKEN health

# Check health
python -m airbyte_cli health

# List sources
python -m airbyte_cli sources list

# Create a source
python -m airbyte_cli sources create --name "My Source" --workspace-id ws123 --type postgres --config @config.json
```

## Authentication

Uses the client credentials flow (`POST /applications/token`) with automatic token
caching and refresh. Also supports a direct bearer token via `--token` flag or
`AIRBYTE_TOKEN` environment variable.

## Configuration Priority

CLI flags > Environment variables > Config file (`~/.config/airbyte-cli/config.json`)

## Commands

| Resource | Actions |
|---|---|
| `sources` | list, get, create, update, replace, delete, oauth |
| `destinations` | list, get, create, update, replace, delete |
| `connections` | list, get, create, update, delete |
| `jobs` | list, get, trigger, cancel |
| `workspaces` | list, get, create, update, delete, oauth |
| `streams` | get |
| `permissions` | list, get, create, update, delete |
| `organizations` | list, oauth |
| `users` | list |
| `source_definitions` | list, get, create, update, delete |
| `destination_definitions` | list, get, create, update, delete |
| `declarative_source_definitions` | list, get, create, update, delete |
| `tags` | list, get, create, update, delete |
| `applications` | list, get, create, delete, token |
| `health` | check |
| `config` | set, show |

## Output Formats

Controlled via the `--format` flag:

| Format | Description |
|---|---|
| `json` | Default. Full JSON — optimal for agent consumption. |
| `table` | Human-readable tabular output. |
| `compact` | Single-line per record — pipe-friendly. |

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | API error |
| 2 | Auth error |
| 3 | Config error |
| 4 | Network error |

## Architecture

Plugin-based modular architecture. Each resource lives in its own package under
`airbyte_cli/plugins/` and registers its subcommands independently. The core layer
handles authentication, HTTP, config, and output formatting. Adding a new resource
requires only a new plugin package — no changes to the core.

## Testing

```bash
python -m unittest discover -s tests -v
```

## Agent & Skills

The `agent/` directory contains a Claude Code agent definition and skills for
AI-driven Airbyte management:

- **manage-sources** — create, inspect, and update sync sources
- **manage-destinations** — configure sync destinations
- **manage-connections** — wire sources to destinations and manage sync schedules
- **manage-jobs** — trigger, monitor, and cancel sync jobs
- **manage-workspaces** — workspace provisioning and settings
- **diagnose** — investigate failed syncs and surface root causes

## License

Internal tool / proprietary.
