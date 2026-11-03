# Runbook: Database restore (Azure Database for PostgreSQL Flexible Server)

This runbook covers how to restore the Finance Tracker production database
from its automated backups. Read it all the way through before you start a
real restore.

## Backup configuration (source of truth: `infra/main.tf`)

| Setting | Value |
| --- | --- |
| Server | `psql-fin-test-3` (`azurerm_postgresql_flexible_server.postgresql`) |
| Resource group | `fin-test-3` |
| Primary region | `uksouth` |
| Engine | PostgreSQL 16 |
| Automated backups | On (managed by Azure, daily snapshots plus continuous WAL archiving) |
| Retention | 35 days (`backup_retention_days = 35`) |
| Geo-redundant backup | On (`geo_redundant_backup_enabled = true`). Backups are copied to the paired region, `ukwest` |
| Point-in-time restore (PITR) | Any point within the 35-day retention window |
| Network | Private only (`public_network_access_enabled = false`), reached through private endpoint `pe-psql-fin-test-3` |

Notes:

- `geo_redundant_backup_enabled` can only be set when the server is created.
  If you change it in Terraform, the server is destroyed and recreated. Do not
  turn it off.
- The app reads its database connection from `POSTGRES_HOST`, `POSTGRES_PORT`,
  `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD`
  (`backend/config/settings/base.py`).

## When to use which restore

| Situation | Procedure |
| --- | --- |
| Data was deleted or corrupted (a bad migration, a mistaken delete) and the primary region is healthy | [A. Point-in-time restore](#a-point-in-time-restore-same-region) |
| The `uksouth` region or the server itself is unavailable | [B. Geo-restore](#b-geo-restore-paired-region) |

Neither restore writes over the existing server. Both create a **new**
server, and you then move the app over to it (section C).

## Prerequisites

- Azure CLI signed in (`az login`) with Contributor rights on resource group
  `fin-test-3` and on the hub resource group that holds the
  `privatelink.postgres.database.azure.com` private DNS zone.
- `psql` on a host that can reach the private network (a jump box or
  self-hosted runner joined to the VNet).
- The admin password from Terraform state (`random_password.postgresql_admin`)
  or from the secret store the deploy uses. A restored server keeps the source
  server's admin login and password.
- An incident ticket, and a record of the exact UTC time just before the
  incident (needed for PITR).

## A. Point-in-time restore (same region)

1. Choose the restore point in UTC. It must fall inside the last 35 days and
   come before the bad change, for example `2026-11-03T09:55:00Z`.
2. Check that the source server's backups exist and note its earliest restore
   point:

   ```bash
   az postgres flexible-server backup list \
     --resource-group fin-test-3 --name psql-fin-test-3 -o table
   ```

3. Restore to a new server:

   ```bash
   az postgres flexible-server restore \
     --resource-group fin-test-3 \
     --name psql-fin-test-3-pitr-<yyyymmddhhmm> \
     --source-server psql-fin-test-3 \
     --restore-time "<restore-point-UTC>"
   ```

   If you leave out `--restore-time`, the CLI restores to the current time
   (the latest restorable point).
4. Wait for provisioning to finish. On this SKU it usually takes 10–30
   minutes:

   ```bash
   az postgres flexible-server show \
     --resource-group fin-test-3 --name psql-fin-test-3-pitr-<yyyymmddhhmm> \
     --query state -o tsv   # expect "Ready"
   ```

5. Go to [C. Reconnect and verify](#c-reconnect-and-verify).

## B. Geo-restore (paired region)

Use this only when the primary server or region is unavailable. Geo-redundant
backups lag the primary by up to about 1 hour (RPO). The restore usually takes
under 12 hours (RTO), depending on database size.

1. Get the source server's resource ID. If the control plane is reachable this
   works, and the ID is
   `/subscriptions/<subscription-id>/resourceGroups/fin-test-3/providers/Microsoft.DBforPostgreSQL/flexibleServers/psql-fin-test-3`:

   ```bash
   az postgres flexible-server show \
     --resource-group fin-test-3 --name psql-fin-test-3 --query id -o tsv
   ```

2. Geo-restore into the paired region:

   ```bash
   az postgres flexible-server geo-restore \
     --resource-group fin-test-3 \
     --name psql-fin-test-3-geo-<yyyymmddhhmm> \
     --source-server "<source-server-resource-id>" \
     --location ukwest
   ```

3. A private endpoint has to sit in a subnet in the same region as the
   server, so a `ukwest` server needs a `ukwest` subnet for its private
   endpoint. If none exists, create one before step C. Follow the pattern of
   `azurerm_private_endpoint.postgresql_pe` in `infra/main.tf`.
4. Wait for the `Ready` state as in A.4, then go to C.

## C. Reconnect and verify

1. **Network.** The restored server is a new resource and has no private
   endpoint yet. Create one into the app subnet (same settings as
   `azurerm_private_endpoint.postgresql_pe`: subresource `postgresqlServer`,
   DNS zone group on `privatelink.postgres.database.azure.com`). Keep public
   network access disabled.
2. **Verify the data** before sending traffic to the server:

   ```bash
   psql "host=<restored-server>.postgres.database.azure.com port=5432 \
         dbname=<POSTGRES_DB> user=psqladmin sslmode=require" \
     -c "select count(*) from django_migrations;" \
     -c "select max(created_at) from transactions_transaction;"
   ```

   Check that the latest `created_at` matches the restore point you chose and
   that `django_migrations` holds the expected latest migration for each app.
3. **Cut over.** Point `POSTGRES_HOST` for the backend at the restored server
   and redeploy or restart the backend. Smoke-test sign-in, the transaction
   list and the dashboard.
4. **Reconcile Terraform.** Terraform still tracks `psql-fin-test-3`. Then do
   one of the following:
   - If the original server is healthy (the PITR case): copy the recovered
     data back into it with `pg_dump`/`pg_restore`, switch `POSTGRES_HOST`
     back, and delete the temporary server. Or
   - Adopt the restored server: update `name`/`location` in `infra/main.tf`,
     `terraform import` the new server and its private endpoint, remove the
     old resources from state, and get the change reviewed. Confirm that
     `backup_retention_days = 35` and `geo_redundant_backup_enabled = true`
     are still set on the adopted server.
5. **Close out.** Record the restore in the log below and in the incident
   ticket, with the restore point, RPO/RTO achieved and any data lost.

## Restore test log

A restore must be tested before go-live and at least once a quarter after
that. Run procedure A against a throwaway server name
(`psql-fin-test-3-restoretest-<date>`) and complete C.2 (data checks only,
no cut-over). Then delete the test server:

```bash
az postgres flexible-server delete \
  --resource-group fin-test-3 --name psql-fin-test-3-restoretest-<date> --yes
```

Add one row per test. Do not add a row until the test has actually been run.

| Date (UTC) | Type (PITR / geo) | Restore point | Restored server | Time to Ready | Data checks passed | Performed by | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| _pending: pre-go-live test not yet performed_ | | | | | | | |
