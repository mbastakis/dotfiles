# TrueNAS Shares

Code-managed NFS and SMB service state with bounded exports required by documented homeserver workflows.

The `deevus/truenas` provider does not expose NFS or SMB shares and service state, so the typed share reconcilers call `sharing.nfs.*`, `sharing.smb.*`, and `service.*` through `midclt` over SSH. The declarations validate offline against their committed JSON Schemas.

## Immich Export

| Field | Value |
|---|---|
| Path | `/mnt/pool_4tb/homeserver/data/photos/immich` |
| Allowed host | `192.168.1.19` (atlas wired LAN reservation) |
| Access | Read/write |
| Identity mapping | `apps:apps` (UID/GID 568) |
| NFS at boot | Enabled |

An empty `hosts` and `networks` combination is rejected by the typed model so a declaration cannot accidentally create a wildcard export. The reconciler compares only declared fields, ignores unrelated NFS shares, and deletes only paths explicitly listed in `retire_shares`.

Dataset creation, ownership, and the `.immich-storage` sentinel remain OpenTofu-owned. Apply OpenTofu before the NFS export.

## Temporary Apple Migration Share

`apple-originals` exposes only `/mnt/pool_4tb/homeserver/data/photos/apple-originals` during the Apple Photos migration. It is non-browsable, rejects guest access, authenticates only the `mbastakis` SMB account, and maps writes to `apps:apps` so the dataset's OpenTofu-owned permissions remain unchanged. The share is removed in code after migration, reconciliation, and restore acceptance; the archive and its Backrest policy remain.

## Commands

```bash
mise exec -- task truenas:nfs:plan
mise exec -- task truenas:nfs:apply
mise exec -- task truenas:smb:plan
mise exec -- task truenas:smb:apply
```
