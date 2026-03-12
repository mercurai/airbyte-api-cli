---
name: manage-connections
description: Guide through connecting an existing Airbyte source to a destination
disable-model-invocation: true
---

# Manage Connections

## Prerequisites

Both a source and a destination must already exist. If either is missing, invoke
the /manage-sources or /manage-destinations skill first.

## Steps

### 1. List available sources

```bash
python -m airbyte_cli sources list
```

Ask the user to identify the `sourceId` they want to connect from.

### 2. List available destinations

```bash
python -m airbyte_cli destinations list
```

Ask the user to identify the `destinationId` they want to connect to.

### 3. Determine stream configuration

For a new connection, ask the user which streams (tables/endpoints) they want to sync
and what sync mode to use per stream:

- **full_refresh | overwrite**: Replace all data on each sync
- **full_refresh | append**: Append all records on each sync
- **incremental | append**: Only sync new/changed records, append to destination
- **incremental | deduped_history**: Only sync new/changed records, deduplicate at destination

If editing an existing connection, retrieve its current stream config first:

```bash
python -m airbyte_cli streams get --connection-id <connection_id>
```

### 4. Determine sync schedule

Ask the user how often to sync. Common options:

- **manual**: Only sync when explicitly triggered
- **cron**: Sync on a cron schedule (e.g., `0 * * * *` for hourly)
- **basic_schedule**: Every N hours/days (e.g., every 24 hours)

### 5. Create the connection

```bash
python -m airbyte_cli connections create \
  --source-id "<source-id>" \
  --destination-id "<destination-id>" \
  --name "<connection-name>" \
  --schedule-type <manual|cron|basic_schedule> \
  --schedule-value "<cron-or-interval>"
```

Note the `connectionId` returned in the response.

### 6. Trigger initial sync (optional)

If the user wants to run an immediate sync after creating the connection:

```bash
python -m airbyte_cli jobs trigger --connection-id <connection-id> --type sync
```

Note the `jobId` returned. Use /sync-status to monitor progress.
