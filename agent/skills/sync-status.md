---
name: sync-status
description: Check the status of running and recent Airbyte sync jobs
---

# Skill: Sync Status

Trigger phrases: "sync status", "job status", "check sync", "list jobs"

## Steps

### 1. List recent jobs

If the user has a specific connection in mind:

```bash
python -m airbyte_cli jobs list --connection-id <connection-id>
```

To see jobs across all connections:

```bash
python -m airbyte_cli jobs list
```

This returns a list of recent jobs with their IDs, types, statuses, and timestamps.

### 2. Get details for a specific job

If the user provides a job ID, or if you want details on a job from the list:

```bash
python -m airbyte_cli jobs get --id <job-id>
```

### 3. Present a status summary

From the job details, present a clear summary to the user:

| Field           | Value                          |
|-----------------|-------------------------------|
| Job ID          | `<job-id>`                    |
| Type            | sync / reset / check          |
| Status          | running / succeeded / failed  |
| Started at      | `<timestamp>`                 |
| Duration        | `<elapsed-time>`              |
| Records synced  | `<count>`                     |
| Bytes synced    | `<bytes>`                     |

### 4. Poll running jobs (optional)

If the job is in a `running` or `pending` state, ask the user if they want to poll
until the job completes. If yes, re-run:

```bash
python -m airbyte_cli jobs get --id <job-id>
```

at a reasonable interval (every 10-30 seconds) and update the user on progress until
the status changes to `succeeded` or `failed`.

### 5. Handle failed jobs

If any job has status `failed`, offer to run the troubleshoot skill to diagnose
the root cause. The relevant connection ID and job ID should be passed to that skill.
