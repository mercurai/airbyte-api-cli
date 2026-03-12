---
name: setup-connection
description: Full end-to-end workflow to set up a new Airbyte pipeline from scratch
---

# Skill: Setup Connection (End to End)

Trigger phrases: "set up airbyte", "new airbyte pipeline", "full sync setup", "end to end setup"

This skill walks through the entire pipeline setup from health check to monitored first sync.

## Steps

### 1. Check API health

```bash
python -m airbyte_cli health
```

If the health check fails, stop here. Ask the user to verify their Airbyte instance URL
and credentials before proceeding.

### 2. Select or create a workspace

List existing workspaces:

```bash
python -m airbyte_cli workspaces list
```

If the user wants to use an existing workspace, note its `workspaceId`. If they want
a new workspace, ask for the name and create it before continuing.

### 3. Create the source

Follow the manage-sources skill steps:

1. List source definitions: `python -m airbyte_cli source_definitions list --limit 100`
2. Ask the user to select a source type and provide connection config.
3. Write config to `config.json` and create:
   ```bash
   python -m airbyte_cli sources create \
     --name "<source-name>" \
     --workspace-id "<workspace-id>" \
     --type "<sourceDefinitionId>" \
     --config @config.json
   ```
4. Verify: `python -m airbyte_cli sources get --id <source-id>`
5. Note the `sourceId`.

### 4. Create the destination

Follow the manage-destinations skill steps:

1. List destination definitions: `python -m airbyte_cli destination_definitions list --limit 100`
2. Ask the user to select a destination type and provide connection config.
3. Write config to `config.json` and create:
   ```bash
   python -m airbyte_cli destinations create \
     --name "<destination-name>" \
     --workspace-id "<workspace-id>" \
     --type "<destinationDefinitionId>" \
     --config @config.json
   ```
4. Verify: `python -m airbyte_cli destinations get --id <destination-id>`
5. Note the `destinationId`.

### 5. Create the connection

Ask the user to choose streams, sync modes, and schedule. Then create:

```bash
python -m airbyte_cli connections create \
  --source-id "<source-id>" \
  --destination-id "<destination-id>" \
  --name "<connection-name>" \
  --schedule-type <manual|cron|basic_schedule> \
  --schedule-value "<cron-or-interval>"
```

Note the `connectionId`.

### 6. Trigger the initial sync

```bash
python -m airbyte_cli jobs trigger --connection-id <connection-id> --type sync
```

Note the `jobId`.

### 7. Monitor until complete

Use the sync-status skill to poll the job until it reaches `succeeded` or `failed`:

```bash
python -m airbyte_cli jobs get --id <job-id>
```

Report a final summary: records synced, bytes transferred, duration, and status.
If the job failed, invoke the troubleshoot skill with the connection ID and job ID.
