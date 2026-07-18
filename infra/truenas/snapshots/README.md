# ZFS Snapshot Tasks

Code-managed ZFS periodic snapshot schedules for the homeserver Obsidian, durable photo, Audiobookshelf state, and book-media datasets.

The TrueNAS Terraform provider (`deevus/truenas` ~> 0.16.0) does not support snapshot tasks (`pool.snapshottask.*`), so these are managed through the TrueNAS API via `midclt` over SSH — following the same pattern as `manage-apps`.

## Owns

- Periodic snapshot task schedules (hourly, daily, weekly)
- Retention lifetime per task
- Naming schema per task

## Does Not Own

- Dataset creation (owned by `infra/truenas/tofu/datasets.tf`)
- One-off snapshots (manual or via `zfs snapshot`)
- Snapshot restore (runbook procedure)

## Schedule

| Task | Frequency | Retention | Naming Schema |
|---|---|---|---|
| hourly | every hour at :00 | 24 hours | `auto-%Y-%m-%d_%H-%M` |
| daily | daily at 00:00 | 14 days | `auto-%Y-%m-%d_%H-%M_daily` |
| weekly | Sunday at 00:00 | 8 weeks | `auto-%Y-%m-%d_%H-%M_weekly` |

The same hourly/daily/weekly schedule is recursive on both `pool_4tb/homeserver/data/obsidian` and `pool_4tb/homeserver/data/photos`. The photo parent captures the Immich media and Apple originals child datasets. Audiobookshelf app state has weekly and monthly recovery points; the mostly static book library has monthly recovery points only.

## Files

| Path | Purpose |
|---|---|
| `snapshot-tasks.yaml` | Versioned task definitions with bounded ownership, stable IDs, schedule, retention, and naming |
| `photo-snapshot-tasks.yaml` | Matching schedule for the recursive durable photo parent dataset |
| `audiobookshelf-snapshot-tasks.yaml` | Weekly and monthly snapshots for Audiobookshelf app state |
| `books-snapshot-tasks.yaml` | Monthly snapshots for the durable book library |
| `manage-snapshots` | Thin shim over the typed TrueNAS snapshot reconciler |

The declaration validates against `infra/schemas/truenas-snapshots.schema.json`.
Run `task infra:desired:validate` for offline validation; no TrueNAS API is
needed. Snapshot task `id` values are stable plan keys, while `naming_schema`
matches the existing remote tasks. Runtime fields such as task state, schedule
windows, and VMware flags are ignored. Tasks on other datasets are outside the
ownership boundary; undeclared tasks on the managed dataset are reported stale
and are deleted only by an explicit `--prune` apply.

## Commands

```bash
task truenas:snapshots:plan
task truenas:snapshots:apply
task truenas:snapshots:apply -- --prune
task truenas:snapshots:photos:plan
task truenas:snapshots:photos:apply
task truenas:snapshots:audiobookshelf:plan
task truenas:snapshots:audiobookshelf:apply
task truenas:snapshots:books:plan
task truenas:snapshots:books:apply
```

## Recovery

To restore from a ZFS snapshot:

```bash
# List available snapshots
ssh truenas "sudo zfs list -t snapshot -o name,creation -s creation"

# Roll back to a specific snapshot (destroys newer snapshots)
ssh truenas "sudo zfs rollback pool_4tb/homeserver/data/obsidian/test@auto-2026-07-09_14-00"
```

For file-level restore without rollback, clone the snapshot or copy individual files from `.zfs/snapshot/` within the dataset.
