---
name: manage-destinations
description: Guide through listing, creating, and verifying Airbyte destinations
disable-model-invocation: true
---

# Manage Destinations

## Steps

### 1. Check API health

```bash
python -m airbyte_cli health
```

If health check fails, stop and tell the user to verify their Airbyte instance is running
and that credentials/base URL are configured correctly.

### 2. List workspaces

```bash
python -m airbyte_cli workspaces list
```

Ask the user to confirm which workspace ID to use if more than one is returned.

### 3. List available destination definitions

```bash
python -m airbyte_cli destination_definitions list
```

Ask the user to select the destination type (e.g., BigQuery, Snowflake, Postgres, S3)
and note the `destinationDefinitionId` for the chosen type.

### 4. Gather destination configuration

Ask the user for the required configuration fields for the chosen destination type.
Common fields vary by type:

- **Postgres**: host, port, database, username, password, schema
- **BigQuery**: project_id, dataset_id, credentials_json
- **Snowflake**: host, role, warehouse, database, schema, username, password
- **S3**: s3_bucket_name, s3_bucket_region, access_key_id, secret_access_key

Collect values from the user and place them in a local `config.json` file. Do not
log sensitive values.

Example `config.json` for a Postgres destination:

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "warehouse",
  "username": "loader",
  "password": "secret",
  "schema": "public"
}
```

### 5. Create the destination

```bash
python -m airbyte_cli destinations create \
  --name "<destination-name>" \
  --workspace-id "<workspace-id>" \
  --type "<destinationDefinitionId>" \
  --config @config.json
```

Note the `destinationId` returned in the response.

### 6. Verify the destination was created

```bash
python -m airbyte_cli destinations get --id <new_destination_id>
```

Confirm the destination status is valid and the connection test passes. If the test
fails, review the config values and repeat from step 4.
