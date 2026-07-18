# Backrest Plans

Code-owned Backrest repository and plan policy for homeserver S3/restic backups.

The Backrest catalog app itself is installed by `infra/truenas/apps/`. Backrest's internal `config.json` is not templated because it contains runtime fields such as the repository GUID, config `modno`, auth state, and multihost identity. `manage-backrest` reconciles durable repo/plan policy through the Backrest API instead.

## Owns

- Repository ID, URI, restic password placeholder, S3 environment placeholders.
- Backup plans, source paths, schedules, and retention.
- Repo-level prune and check schedules.
- Retirement of the legacy combined plan `homeserver-files-obsidian-weekly`.
- Typed secret references for the three environment placeholders; values remain outside Git and validation.

## Does Not Own

- Backrest app install values and host-path mounts; those live in `infra/truenas/apps/declarations/backrest.yaml`.
- Backrest auth users/password hashes.
- Repository GUID, operation history, indexes, cache, logs, and multihost identity.
- Restic repository contents in S3.

## Repository

| Field | Value |
|---|---|
| Repository | `homeserver-s3` |
| URI | `s3:s3.eu-central-1.amazonaws.com/mbastakis-homeserver-restic-backups/truenas` |
| Password | `RESTIC_PASSWORD=${RESTIC_PASSWORD}` in repo env from the Backrest app environment |
| AWS credentials | `${AWS_ACCESS_KEY_ID}` and `${AWS_SECRET_ACCESS_KEY}` in repo env from the Backrest app environment |
| Upload limit | `6000 KiB/s` (about `49.2 Mb/s`, just under half of the `100 Mb/s` WAN upload capacity) |
| Prune | Quarterly on day 1 at 05:00 local time, `maxUnusedPercent` 10 |
| Check | Monthly on day 2 at 06:00 local time, structure-only |

## Plans

| Plan | Path | Schedule | Retention |
|---|---|---|---|
| `homeserver-files-daily` | `/source/files` | Daily 01:15 local | 14 daily, 8 weekly, 24 monthly, 5 yearly |
| `homeserver-obsidian-daily` | `/source/obsidian` | Daily 02:15 local | 30 daily, 8 weekly, 24 monthly, 5 yearly |
| `homeserver-immich-daily` | `/source/immich` | Daily 02:30 local | 14 daily, 8 weekly, 24 monthly, 5 yearly |
| `homeserver-apple-originals-daily` | `/source/apple-originals` | Daily 03:00 local | 14 daily, 8 weekly, 24 monthly, 5 yearly |
| `homeserver-taskchampion-daily` | `/source/taskchampion-sync-backup` | Daily 04:30 local | 14 daily, 8 weekly, 12 monthly, 3 yearly |
| `homeserver-audiobookshelf-weekly` | `/source/audiobookshelf-backups` | Sunday 03:30 local | 8 weekly, 12 monthly |
| `homeserver-books-monthly` | `/source/books` | Monthly on day 1 at 04:30 local | 6 monthly, 3 yearly |

The Immich plan runs after Immich writes its native PostgreSQL dump into
`/data/backups` at 02:00. `/source/immich` contains durable media and those
database dumps; Atlas-local thumbnails, encoded videos, caches, and live
PostgreSQL files are excluded because derived media is regenerated and the
database is restored from the dump. The Apple originals plan uses
`skipIfUnchanged`, so the stable archive does not produce redundant snapshots.
The TaskChampion plan runs after the atlas `taskchampion-backup.timer` copies
the SQLite backup to TrueNAS at 03:00. The Audiobookshelf plan runs after the
application creates its weekly archive at 02:00; the book-media plan is
intentionally monthly and should be run manually after a large import when a
month of exposure is unacceptable.

## Commands

```bash
mise exec -- task truenas:backrest:validate
mise exec -- task truenas:backrest:plan
mise exec -- task truenas:backrest:apply
```

The Task plan/apply commands inject the `truenas-backrest` BWS target
automatically. The typed reconciler compares only declared repository fields,
preserves the runtime GUID and top-level config, keeps undeclared plans with a
warning, and removes only IDs listed in `retirePlans`.

The upload limit is a repository-level restic flag, so every S3-writing
operation is bounded without limiting restores or unrelated homeserver traffic.
Backrest serializes its normal scheduled and manual backup queue, making this a
single aggregate cap for the managed plans. Do not run a concurrent external
restic process or use Backrest's unrestricted Run Command path when the cap must
be preserved; each separate process has its own limiter.

On the home LAN, plan/apply use the direct TrueNAS Backrest app URL. Outside the LAN, the wrapper automatically opens a temporary local port forward through the `atlas` SSH alias to the TrueNAS LAN endpoint because the Tailscale ACL intentionally denies direct client access to raw Backrest port `30329` and TrueNAS OpenSSH disables forwarding. The tunnel and control socket are removed when the reconciler exits. Set `BACKREST_URL` to bypass automatic routing when needed.

`backrest-plans.yaml` declares schema version 1, bounded ownership, stable
repository/plan IDs, and typed `secret_ref` aliases. It validates offline
against `infra/schemas/backrest.schema.json` through
`task infra:desired:validate`; that command does not contact Backrest or BWS.

## 3-2-1 Model

This policy follows the 3-2-1 backup principle for durable homeserver data:

- Primary copy: live TrueNAS datasets under `pool_4tb/homeserver/data` plus application-consistent Audiobookshelf archives under `pool_4tb/homeserver/apps/audiobookshelf/backups`.
- Local recovery copy: ZFS snapshots for fast rollback from mistakes or local corruption.
- Offsite copy: encrypted restic repository in S3, orchestrated by Backrest.

The two storage media/classes are local ZFS storage and S3 object storage. The offsite copy is S3. Obsidian also has Syncthing device replicas, but those are treated as sync replicas, not as the backup authority. Photo plans cover durable Immich media, logical database dumps stored there, and the Apple originals archive; atlas-local thumbnails, transcodes, and machine-learning cache remain excluded.

If stricter physical-media isolation is needed later, add a second local restic target such as a removable USB disk or another NAS. The current pool-local snapshots protect against deletion/corruption, not complete pool failure.
