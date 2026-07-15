# Restore from ZFS Snapshot

ZFS snapshots are the primary recovery path for mistakes and local data
loss. They are fast (seconds), local (no S3 involved), and recursive
across the `pool_4tb/homeserver/data/obsidian` dataset tree.

## Snapshot schedule

Managed by `infra/truenas/snapshots/snapshot-tasks.yaml`:

| Task    | Retention | Schedule             |
|---------|-----------|----------------------|
| hourly  | 24 hours  | every hour at :00    |
| daily   | 14 days   | daily at 00:00       |
| weekly  | 8 weeks   | weekly on Sunday 00:00 |

All snapshots are recursive and named `auto-%Y-%m-%d_%H-%M[_daily|_weekly]`.

## Prerequisites

- SSH access to truenas (`ssh truenas`).
- `homeserver-admins` Tailscale access.

## List available snapshots

```bash
ssh truenas "sudo zfs list -t snapshot -o name,creation,refer -r pool_4tb/homeserver/data/obsidian"
```

## Restore a single file

Snapshots are accessible under the `.zfs/snapshot/` directory at the
dataset root. This is the fastest restore method:

```bash
# Find the file in a snapshot
ssh truenas "ls /mnt/pool_4tb/homeserver/data/obsidian/michail/.zfs/snapshot/auto-2025-07-09_00-00_daily/"

# Copy it back
ssh truenas "sudo cp /mnt/pool_4tb/homeserver/data/obsidian/michail/.zfs/snapshot/auto-2025-07-09_00-00_daily/lost-note.md /mnt/pool_4tb/homeserver/data/obsidian/michail/"
```

> TrueNAS hides `.zfs` from `ls -a` by default but the path is
> accessible. Use the full path directly.

## Restore an entire dataset (rollback)

Rollback reverts the dataset to the snapshot state, discarding all
changes made after the snapshot. Use with caution.

```bash
# Stop Syncthing to avoid conflicts
ssh truenas "sudo midclt call app.stop syncthing"

# Rollback
ssh truenas "sudo zfs rollback pool_4tb/homeserver/data/obsidian/michail@auto-2025-07-09_00-00_daily"

# Start Syncthing
ssh truenas "sudo midclt call app.start syncthing"
```

After rollback, Syncthing will detect the reverted state and propagate
it to other peers. If this is not desired, pause Syncthing on other
peers first and resume after verifying the rollback.

## Restore without rollback (copy from snapshot)

Safer than rollback — copies the entire snapshot contents to a temp
directory for selective recovery:

```bash
ssh truenas "sudo cp -a /mnt/pool_4tb/homeserver/data/obsidian/michail/.zfs/snapshot/auto-2025-07-09_00-00_daily/ /mnt/pool_4tb/homeserver/data/obsidian/restored/"

# Inspect and selectively copy files back
ssh truenas "sudo rsync -av /mnt/pool_4tb/homeserver/data/obsidian/restored/ /mnt/pool_4tb/homeserver/data/obsidian/michail/"

# Clean up
ssh truenas "sudo rm -rf /mnt/pool_4tb/homeserver/data/obsidian/restored"
```

## Restore test checklist

When running a periodic restore test (spec Phase 4 acceptance):

- [ ] Create a test file in the Obsidian vault.
- [ ] Wait for the next hourly snapshot (or create one manually:
      `ssh truenas "sudo zfs snapshot pool_4tb/homeserver/data/obsidian/michail@manual-test"`).
- [ ] Delete the test file.
- [ ] Restore it from the snapshot using `.zfs/snapshot/`.
- [ ] Verify the file content matches.
- [ ] Clean up any manual test snapshots:
      `ssh truenas "sudo zfs destroy pool_4tb/homeserver/data/obsidian/michail@manual-test"`.

## Notes

- Snapshots are read-only. You cannot modify files inside a snapshot.
- `.zfs/snapshot` access requires the dataset to be mounted (default on
  TrueNAS).
- Rollback to a non-most-recent snapshot requires destroying all
  intermediate snapshots first.
- Snapshot tasks are managed in code — do not create manual snapshot
  tasks through the TrueNAS UI. One-off manual snapshots are fine.
