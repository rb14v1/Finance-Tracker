# Runbook: PostgreSQL Flexible Server restore

This runbook covers restoring the application database `psql-fin-test-3`. The server is defined in
`infra/main.tf` (resource group `fin-test-3`, region `uksouth`).

## Backup configuration (from `infra/main.tf`)

| Setting | Value |
|---|---|
| Automated backups | Enabled (Azure-managed, daily full + continuous WAL) |
| Retention | `backup_retention_days = 35` |
| Geo-redundant backup | `geo_redundant_backup_enabled = true` (copied to the paired region, `ukwest`) |
| Point-in-time recovery | Any point within the 35-day retention window |

Azure Database for PostgreSQL Flexible Server always restores to a **new** server. It never
overwrites the source server. So a restore means you provision a new server, check it, and then
point the application at it.

## Prerequisites

- Azure CLI (`az`) is logged in with Contributor rights on resource group `fin-test-3`, and with
  rights to create private endpoints in the application subnet (`var.subnet_id`).
- You know the target restore time, in UTC ISO-8601 (for example `2026-11-03T09:30:00Z`). It must
  fall inside the retention window. The earliest restore point is shown by:
  ```sh
  az postgres flexible-server show -g fin-test-3 -n psql-fin-test-3 --query "backup.earliestRestoreDate"
  ```
- A name for the restored server, for example `psql-fin-test-3-restore-<yyyymmdd>`.

## Procedure A: point-in-time restore (same region)

Use this for logical corruption, a bad migration or accidental data deletion.

1. **Stop writes.** Scale the backend down, or put it into maintenance, so no more data is written
   after the incident.
2. **Restore to a new server:**
   ```sh
   az postgres flexible-server restore \
     --resource-group fin-test-3 \
     --name psql-fin-test-3-restore-<yyyymmdd> \
     --source-server psql-fin-test-3 \
     --restore-time "<UTC restore time>"
   ```
3. **Restore private connectivity.** The source server has `public_network_access_enabled = false`
   and is reached through private endpoint `pe-psql-fin-test-3`. Create an equivalent private
   endpoint for the restored server in the same subnet (subresource `postgresqlServer`). Register it
   in the `privatelink.postgres.database.azure.com` DNS zone in the hub resource group.
4. **Verify the data.** Connect from inside the VNet, using the admin credentials restored from the
   source server, and check:
   - `SELECT now();` works, and the expected databases exist (`\l`).
   - Row counts and the most recent records in key tables match the chosen restore time.
   - `python manage.py showmigrations` against the restored server shows the expected migration state.
5. **Cut over.** Change the backend's database host setting (read through python-decouple from the
   environment) to the restored server's FQDN. Redeploy or restart the backend, then confirm that
   `GET /healthz` and a smoke test of the authenticated `/api/` endpoints pass.
6. **Bring Terraform back in line.** The restored server is not in Terraform state. Do one of these:
   - Import it in place of the original: `terraform state rm` the old resource, `terraform import`
     the new one, and update `name` in `infra/main.tf` in a reviewed PR.
   - Or, after the incident, restore or copy the data back to `psql-fin-test-3`, then delete the
     temporary server.
7. **Clean up.** Delete the temporary server and private endpoint once you no longer need them.
   Keep the original server until the incident review signs off.

## Procedure B: geo-restore (regional outage)

Use this when `uksouth` is unavailable. Geo-redundant backups can be restored to the paired region:

```sh
az postgres flexible-server geo-restore \
  --resource-group <resource group in ukwest> \
  --name psql-fin-test-3-geo-<yyyymmdd> \
  --source-server $(az postgres flexible-server show -g fin-test-3 -n psql-fin-test-3 --query id -o tsv) \
  --location ukwest
```

Geo-restore recovers to the latest available geo-replicated backup. Expect an RPO of up to about
1 hour. Then follow steps 3 to 7 of Procedure A, using a VNet and subnet reachable in `ukwest`.

## Restore test record

Run a test restore with Procedure A (restore to a temporary server, verify, delete) **before
go-live**. After that, run one at least every 6 months, and after any change to the backup
configuration. Record every test below.

| Date (UTC) | Performed by | Procedure | Restore point | Time to restore | Data verified | Outcome / notes |
|---|---|---|---|---|---|---|
| _pending: pre-go-live test not yet performed_ | | A (PITR) | | | | |
