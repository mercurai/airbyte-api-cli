---
name: troubleshoot
description: Diagnose and fix failed Airbyte syncs by inspecting jobs, connections, sources, and destinations
disable-model-invocation: true
---

# Troubleshoot Failed Syncs

## Steps

### 1. Check API health

Confirm the Airbyte API is reachable before investigating anything else:

```bash
python -m airbyte_api_cli health
```

If the health check itself fails, the issue is infrastructure-level (Airbyte instance
down, network issue, bad credentials). Stop here and report that to the user.

### 2. List recent jobs for the connection

Ask the user for the connection ID if not already known, then fetch recent jobs:

```bash
python -m airbyte_api_cli jobs list --connection-id <connection-id>
```

Identify the most recent failed job and note its `jobId`.

### 3. Get details on the failed job

```bash
python -m airbyte_api_cli jobs get --id <job-id>
```

Look for:
- `failureReason` or `failureOrigin` fields
- Error message text
- Which step failed (replication, normalization, dbt, etc.)
- How far through the sync it got (records synced before failure)

### 4. Check the connection configuration

```bash
python -m airbyte_api_cli connections get --id <connection-id>
```

Verify:
- The connection status is not `deprecated` or `inactive`
- The stream selection and sync modes look correct
- The schedule configuration is valid

### 5. Check the source

```bash
python -m airbyte_api_cli sources get --id <source-id>
```

Look for:
- Connection test status
- Any config validation errors
- Whether credentials may have expired or changed

### 6. Check the destination

```bash
python -m airbyte_api_cli destinations get --id <destination-id>
```

Look for:
- Connection test status
- Schema or permission issues at the destination
- Whether credentials may have expired or changed

### 7. Provide diagnosis

Based on the gathered information, provide a diagnosis. Common failure patterns:

| Symptom | Likely cause | Suggested fix |
|---------|-------------|---------------|
| Auth error in job log | Expired credentials | Update source/destination config |
| Schema mismatch | Destination schema changed | Run a reset then re-sync |
| Timeout during replication | Source query too slow | Reduce sync frequency or split streams |
| Normalization failed | dbt model error | Check normalization logs, adjust stream config |
| Destination write failed | Permissions or disk space | Check destination access rights |

### 8. Offer to reset or re-trigger

If the diagnosis calls for a data reset:

```bash
python -m airbyte_api_cli jobs trigger --connection-id <connection-id> --type reset
```

To re-trigger a normal sync after fixing the underlying issue:

```bash
python -m airbyte_api_cli jobs trigger --connection-id <connection-id> --type sync
```

Use /sync-status to monitor the new job until it completes.
