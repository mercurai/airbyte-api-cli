---
name: manage-sources
description: Guide the user through listing, creating, and verifying Airbyte sources
---

# Skill: Manage Sources

Trigger phrases: "add source", "configure source", "create source", "list sources"

## Steps

### 1. Check API health

Before any source operations, confirm the Airbyte API is reachable:

```bash
python -m airbyte_cli health
```

If health check fails, stop and tell the user to verify their Airbyte instance is running
and that credentials/base URL are configured correctly.

### 2. List workspaces

Identify the workspace to operate in:

```bash
python -m airbyte_cli workspaces list
```

Ask the user to confirm which workspace ID to use if more than one is returned.

### 3. List available source definitions

Show the user what source types are available:

```bash
python -m airbyte_cli source_definitions list --limit 100
```

Ask the user to select the source type (e.g., Postgres, GitHub, Stripe) and note the
`sourceDefinitionId` for the chosen type.

### 4. Gather source configuration

Ask the user for the required configuration fields for the chosen source type. Common
fields include host, port, database name, username, and password. Sensitive values
should be collected from the user and placed in a local `config.json` file.

Example `config.json` for a Postgres source:

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "secret",
  "ssl": false
}
```

### 5. Create the source

```bash
python -m airbyte_cli sources create \
  --name "<source-name>" \
  --workspace-id "<workspace-id>" \
  --type "<sourceDefinitionId>" \
  --config @config.json
```

Note the `sourceId` returned in the response.

### 6. Verify the source was created

```bash
python -m airbyte_cli sources get --id <new_source_id>
```

Confirm the source status is valid and the connection test passes. If the test fails,
review the config values and repeat from step 4.
