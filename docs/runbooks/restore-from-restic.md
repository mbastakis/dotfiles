# Restore from Restic (Backrest/S3)

Off-NAS disaster recovery restore from the encrypted restic repository in
S3. The active repository is `s3:s3.eu-central-1.amazonaws.com/mbastakis-homeserver-restic-backups/truenas`,
managed by the Backrest catalog app on TrueNAS.

Backrest desired repository and plan policy is code-owned in
`infra/truenas/backrest/backrest-plans.yaml`.

## When to use this

- Catastrophic TrueNAS pool loss.
- File deletion or corruption beyond Syncthing versioning and ZFS
  snapshot retention.
- Disaster recovery test (recommended quarterly).

## Prerequisites

- BWS access for `backrest_restic_repo_password`, `backrest_aws_access_key_id`,
  and `backrest_aws_secret_access_key`.
- A machine with `restic` installed and network access to S3.
- TrueNAS may or may not be available — this procedure works from any
  machine with the right credentials.

## Option A: Restore through Backrest UI

Use this when TrueNAS is up and Backrest is reachable.

1. Connect to Tailscale as a `homeserver-admins` user.
2. Open the Backrest UI at `https://backrest.mbastakis.com`.
3. Select the `homeserver-s3` repository.
4. Select the plan that matches the data domain you are restoring.
5. Browse snapshots, select the snapshot to restore from.
6. Choose a restore target:
   - **Restore to original path** overwrites live data — use only for
     targeted file recovery.
   - **Restore to a temp path** (e.g. `/source/obsidian/restored`) for
     safe inspection before moving files.
7. Trigger the restore and monitor progress.
8. If you restored to a temp path, rsync the files to their final
   location:

   ```bash
   ssh truenas "sudo rsync -av /mnt/pool_4tb/homeserver/data/obsidian/restored/ /mnt/pool_4tb/homeserver/data/obsidian/michail/"
   ```

9. Clean up the temp restore directory after verification.

Current plans:

| Data | Backrest plan | Path |
|---|---|---|
| Files | `homeserver-files-daily` | `/source/files` |
| Obsidian | `homeserver-obsidian-daily` | `/source/obsidian` |
| Immich media | `homeserver-immich-daily` | `/source/immich` |
| Apple originals | `homeserver-apple-originals-daily` | `/source/apple-originals` |
| TaskChampion sync backup | `homeserver-taskchampion-daily` | `/source/taskchampion-sync-backup` |

## Option B: Restore with restic CLI

Use this when TrueNAS is down or you prefer CLI control.

1. Resolve secrets from BWS:

   ```bash
   eval "$(infra/secrets/homeserver-secrets exec truenas-backrest -- env)"
   ```

   This sets `RESTIC_PASSWORD`, `AWS_ACCESS_KEY_ID`, and
   `AWS_SECRET_ACCESS_KEY`.

2. List snapshots:

   ```bash
   restic -r s3:s3.eu-central-1.amazonaws.com/mbastakis-homeserver-restic-backups/truenas snapshots
   ```

3. Find the snapshot you need (filter by path or date):

   ```bash
   restic -r s3:s3.eu-central-1.amazonaws.com/mbastakis-homeserver-restic-backups/truenas snapshots --path /source/obsidian
   ```

4. Restore to a local temp directory:

   ```bash
   restic -r s3:s3.eu-central-1.amazonaws.com/mbastakis-homeserver-restic-backups/truenas restore <snapshot-id> --target /tmp/restic-restore
   ```

5. Inspect the restored files and copy what you need to its final
   destination (back to TrueNAS if recovered, or elsewhere).

6. Clean up:

   ```bash
   rm -rf /tmp/restic-restore
   ```

## Restore test checklist

When running a periodic restore test (spec Phase 5 acceptance):

- [ ] Snapshot list is accessible from S3.
- [ ] At least one file restores successfully.
- [ ] Restored file content matches the original (checksum or diff).
- [ ] Document the test date and result in this runbook or an ADR.

## Notes

- S3 storage class is Glacier Instant Retrieval — objects are
  immediately readable without asynchronous restore.
- 90-day minimum storage duration means recently written data may incur
  early-deletion charges if pruned before 90 days. This is expected and
  budgeted.
- The restic repository password is in BWS as
  `backrest_restic_repo_password`. Never commit it.
- The backup model follows 3-2-1 principles: live TrueNAS data, local ZFS
  snapshots for rollback, and encrypted offsite restic snapshots in S3.
