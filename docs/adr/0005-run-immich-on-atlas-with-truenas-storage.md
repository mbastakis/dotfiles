# Run Immich on atlas with TrueNAS storage

**Status:** Accepted; Phase 3 deployment complete (2026-07-11)

## Context

Immich needs application compute, a local database, durable original media, private household access, and independently testable recovery. `atlas` is the Ansible-owned application and ingress host, while `truenas` is the storage authority. Running Immich as a TrueNAS catalog app would move general application compute onto the storage appliance. Keeping all Immich data on atlas would make atlas authoritative for irreplaceable photos. Immich supports NAS-backed media mounted at `/data`, but explicitly requires Postgres to remain on local storage.

## Decision

Immich will run in a dedicated `/opt/homeserver/immich` Compose project on atlas and join the existing external `homeserver` network only for Traefik ingress. Immich server and machine learning will run CPU-only, and video transcoding will use software encoding. The unsupported GeForce GT 650M will not receive a legacy or patched NVIDIA driver for Immich. Postgres, Valkey, thumbnails, encoded videos, and machine-learning cache will remain on atlas under its local `/home` HDD.

TrueNAS will remain authoritative for durable photo data. One dataset, `pool_4tb/homeserver/data/photos/immich`, will be exported over NFS only to atlas's reserved LAN address and mounted at `/data`. Local atlas directories will overlay `/data/thumbs` and `/data/encoded-video`. The NFS mount will use hard, fail-closed semantics, and Immich will not start unless both the real mount and a TrueNAS sentinel are present. Postgres and Valkey will never use NFS.

Unmodified Apple originals, XMP sidecars, manifests, checksums, and reports will live separately at `pool_4tb/homeserver/data/photos/apple-originals`. That archive will not be exported to atlas or registered as an Immich external library. The optimized `.photoslibrary` remains on the Mac; bounded `osxphotos 0.76.1 --download-missing` exports may write directly to a Mac-mounted TrueNAS destination rather than requiring a second full local staging copy. Media will enter Immich only through supported APIs or the official CLI.

ZFS snapshots will provide local rollback. Logical database dumps and durable photo domains will be backed up by Backrest/restic to the existing encrypted `homeserver-s3` repository. Regenerable thumbnails, encoded videos, and machine-learning models will not be sent to S3. Public ingress, router forwarding, Tailscale Funnel, S3 primary storage, and TrueNAS-hosted Immich are rejected.

## Phase 1 Findings

| Gate | Observed state | Result |
|---|---|---|
| Atlas LAN identity | The router reserves `192.168.1.19` for wired MAC `50:46:5d:38:5a:a1`; atlas retained `192.168.1.19/24` after a DHCP lease renewal | Accepted |
| Atlas OS | Ubuntu Server 26.04 LTS, kernel `7.0.0-22-generic` | Recorded |
| NVIDIA GPU | GeForce GT 650M (`GK107M`, PCI `10de:0fd1`), compute capability 3.0, currently using `nouveau` | Recorded; CPU-only processing accepted |
| NVIDIA driver | This mobile Kepler device ends at the legacy R418 branch; Immich v3.0.2 CUDA requires compute capability 5.2+ and driver 545+, while its NVENC stack also requires a newer driver | No Immich NVIDIA driver will be installed |
| Atlas local storage | The 120 GB SATA SSD has 34,982,789,120 bytes free on `/`; the rotating 750 GB HGST disk mounted at `/home` has 696,064,376,832 bytes free | `/home` HDD accepted for local runtime state |
| Atlas memory | 7,202,140,160 bytes total (about 6.7 GiB) with 4 GiB swap | Accepted at Immich's 6 GB minimum, below its 8 GB recommendation |
| TrueNAS capacity | `pool_4tb` is online with 3,985,729,650,688 bytes total, 259,287,072,768 bytes allocated, and 3,726,442,577,920 bytes free (about 6.5% allocated) | Passes preliminary capacity gate |
| Apple inventory | 12,285 assets, including 1,561 videos, 163 Live Photos, 605 edited assets, 128 favorites, no detected RAW assets or RAW+JPEG pairs, 9 regular albums, and 9 shared albums; all assets report as synchronized to iCloud, but 12,277 originals are currently missing from local disk | Inventory accepted; source preparation remains a migration-phase task |
| Apple source size | Photos metadata reports 203,702,487,172 original bytes, while the local optimized Photos package is only about 3.9 GB | Recorded; full download required |
| Migration staging | The Mac has 112,403,103,744 bytes free, less than the reported original-media size before export overhead | Bounded direct-to-TrueNAS exports accepted; no full local staging copy required |
| Existing S3 footprint | 11,597 objects totaling 198,765,164,122 bytes in `mbastakis-homeserver-restic-backups`; conservative photo expansion projects about $3.03/month in storage | Accepted below the $10 review threshold |

The preliminary conservative TrueNAS projection stores both the approximately 203.7 GB original archive and a similarly sized Immich rendition library without assuming deduplication. Including current pool allocation, that is about 666.7 GB, or 16.7% of pool capacity, before modest profile and database-dump overhead. Because the accepted policy now retains rendered edits in both the archive and Immich, the projected bytes must be refreshed from the validated import manifest before bulk approval; the 80% capacity gate remains unchanged.

Atlas needs about 90.7 GB free for the plan's 20% generated-media estimate plus 50 GB operating headroom. The accepted `/home` HDD has about 696 GB free, so it satisfies the revised capacity gate while accepting slower indexing, transcoding, and thumbnail access.

At the current `eu-central-1` Glacier Instant Retrieval storage rate of $0.005 per GB-month, the current S3 footprint is about $0.99/month. The projected repository is roughly $2.01/month if restic deduplicates byte-identical archive and Immich content, and about $3.03/month under a conservative no-deduplication projection. Requests, retrieval, early-deletion charges, Standard-class objects below the lifecycle transition threshold, Live Photo companions, edited renditions, and growth remain additional. The projection is below the $10 review threshold but still requires explicit acceptance before bulk migration.

## Consequences

Phase 2 may create the photo datasets, host-restricted NFS export, snapshot tasks, and Backrest plans. The reduced hardware profile is an explicit tradeoff: initial indexing and video transcodes may be slow, generated-media access will have HDD latency, and memory pressure may use swap. Postgres remains local to atlas and never uses NFS. The deployment must be monitored during migration batches and concurrency reduced before changing the storage boundary.

The Apple migration remains independently gated by manifests, checksums, a pilot import, album/metadata acceptance, restore testing, and explicit deletion approval. Accepting Phase 1 does not authorize deleting iCloud data or the Photos library.

## Phase 2 Implementation

OpenTofu created the `photos`, `photos/immich`, and `photos/apple-originals` datasets with destroy protection. The two durable child datasets use `apps:apps` ownership, and OpenTofu owns the `.immich-storage` sentinel in the Immich dataset.

Because `deevus/truenas` v0.16.0 has no NFS resources, a typed bounded reconciler owns the NFS service and Immich export through TrueNAS middleware. The export is read/write only from `192.168.1.19`, maps all access to `apps:apps`, and leaves unrelated shares unmanaged. A real atlas NFSv4.2 mount verified the hard mount options, sentinel identity, and create/delete access through the export.

Recursive hourly, daily, and weekly snapshots cover the `photos` parent. Backrest mounts each durable child read-only and has separate daily Immich and Apple-originals plans in the existing encrypted `homeserver-s3` repository. Post-apply live plans report no managed drift. No Immich containers or persistent atlas mount units were deployed in Phase 2.

## Phase 3 Implementation

Ansible deploys Immich v3.0.2 as a dedicated `/opt/homeserver/immich` Compose project managed by `immich.service`. A systemd NFS mount and automount use NFSv4.2 hard semantics. Every apply verifies the kernel-reported NFS source and exact `.immich-storage` sentinel before rendering or starting Immich. The service repeats the mountpoint and sentinel gates on every start, binds its lifecycle to the mount unit, and runs Compose attached so Docker daemon restarts cannot bypass the gate.

Postgres, Valkey, thumbnails, encoded video, and machine-learning cache are bind-mounted below `/home/mbastakis/.local/share/immich`. The durable NFS root remains `/data` in the server container, with local nested mounts overlaying `/data/thumbs` and `/data/encoded-video`. The server and machine-learning containers use UID/GID 1000, CPU-only processing, one ML worker, two request threads, and a 120-second model cache TTL. An Ansible-rendered `IMMICH_CONFIG_FILE` enables the date-based storage template, schedules database dumps at 02:00 with 14 retained copies, limits CPU-heavy jobs to concurrency one, restricts software transcoding to two threads, and enables native Authentik OIDC. The protected file is mounted read-only; its client secret comes from BWS. OpenTofu owns the matching Authentik provider, dedicated state-persisted RSA key and self-signed RS256 certificate, callbacks, access policy, and role claim. Only the managed `michail` Authentik identity receives the `admin` claim; all others receive `user`, and the bootstrap `akadmin` identity cannot authorize Immich. The existing `mbastakis@gmail.com` Immich administrator links by email and retains local password login for break-glass access. Global settings are code-owned; user records and OIDC links, storage labels, and mobile-device choices remain runtime-owned. Postgres and Valkey remain isolated on the Immich network; an explicit `immich-valkey` alias avoids collision with the existing Authentik Redis service on the shared ingress network.

Route53 points `photos.mbastakis.com` at atlas's Tailscale address. Traefik reaches only `immich-server:2283` through the existing external `homeserver` network; no Immich port is published directly. All four containers report healthy, the server reports v3.0.2, Immich's storage integrity checks pass, and private HTTPS returns the expected server ping. The built-in daily logical database backups land in the durable `/data/backups` domain already covered by the Immich Backrest plan.

Phase 3 does not authorize bulk Apple Photos export, import, or source deletion. The migration gates in this ADR remain in force.

## Phase 4 Migration Preparation

A fresh read-only source count on 2026-07-12 found 12,281 Photos database records: 8,414 visible personal assets, 10 hidden personal assets, and 3,857 shared-album assets. All 8,424 personal originals are absent from the optimized local library, so the migration continues to require a direct-to-TrueNAS export rather than local staging.

The typed share runtime now owns a temporary `apple-originals` SMB export for the migration. The share exposes only the dedicated archive dataset, is non-browsable, rejects guest access, authenticates only the `mbastakis` TrueNAS account, and maps all file operations to `apps:apps` without changing the OpenTofu-owned dataset permissions. The SMB service and share report no managed drift after apply. This export must remain only through export, reconciliation, and restore acceptance, then be explicitly retired in code while the archive, snapshots, and Backrest policy remain.

The representative pilot exposed Traefik's default 60-second request-body read timeout when a 133 MB video returned `502 Bad Gateway` while smaller files succeeded. The private `websecure` entrypoint now allows a finite three-hour active request read and ten-minute idle connection window so large current and future mobile uploads can complete without adding a buffering middleware or body-size cap.

The ten-record pilot produced 49 archive files and 17 physical media files. Dates, GPS metadata, XMP sidecars, checksum deduplication, and two Live Photo pairings passed. Two first-pass iCloud originals were actually Apple adjustment XML plists under `.MOV` and `.HEIC` names despite a successful osxphotos report; isolated repeat retrieval produced valid media, and the invalid files were quarantined. Bulk export therefore requires independent media-magic validation, UUID-based retry, and SHA-256 verification rather than trusting extensions or export-database signatures.

The pilot also confirmed that importing both representations creates separate timeline entries for adjusted media such as Cinematic video because Immich has no generic relationship for an Apple original and rendered edit. This is accepted: both validated renditions will remain in the permanent archive and Immich. A manifest-driven official API dry run will test grouping original/edit sets with Immich stacks, using the rendered edit as primary, and will map source favorites and the nine regular albums after upload. Hidden-asset and shared-album handling remain unresolved; osxphotos v0.76.1 cannot reliably export shared albums on macOS 26. Bulk migration remains paused pending those decisions, rendition/stack and metadata dry-run tooling, refreshed capacity projection, and pilot backup/restore acceptance. The detailed resume gates are in the [Apple Photos to Immich migration runbook](../runbooks/apple-photos-immich-migration.md).

## References

- [Immich v3.0.2 machine-learning hardware acceleration](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/docs/docs/features/ml-hardware-acceleration.md#L43-L46)
- [Immich v3.0.2 hardware transcoding](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/docs/docs/features/hardware-transcoding.md#L34-L37)
- [Immich v3.0.2 configuration file](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/docs/docs/install/config-file.md)
- [Immich v3.0.2 OAuth](https://github.com/immich-app/immich/blob/v3.0.2/docs/docs/administration/oauth.md)
- [Authentik Immich integration](https://integrations.goauthentik.io/media/immich/)
- [NVIDIA legacy CUDA GPU table](https://developer.nvidia.com/cuda-legacy-gpus)
- [NVIDIA R418 supported products](https://us.download.nvidia.com/XFree86/Linux-x86_64/418.113/README/supportedchips.html)
- [NVIDIA R545 supported products](https://us.download.nvidia.com/XFree86/Linux-x86_64/545.29.06/README/supportedchips.html)
