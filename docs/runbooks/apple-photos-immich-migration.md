# Apple Photos to Immich Migration

**Status:** Pilot and ten-hidden-asset validation/import gates passed. The
canonical personal export is active and resumable: 4,947 of the frozen 8,424
source UUIDs have successful export-database coverage, leaving 3,477 unresolved
as of 2026-07-13. Bulk Immich import has not started beyond the 17 validated
hidden renditions.

This runbook preserves the migration evidence and gates for moving the personal Apple Photos library into Immich. The permanent Apple archive and the user-facing Immich timeline have different fidelity goals and must not use the same unfiltered media set.

## Current Inventory

The read-only 2026-07-12 source manifest contains 8,424 personal assets: 7,369 photos, 1,055 videos, 77 Live Photos, 605 edited assets, 128 favorites, 10 hidden assets, 5,975 assets with coordinates, and no RAW assets. The Photos database additionally contains 3,857 shared-album records. That shared-album count is inventory evidence only: osxphotos v0.76.1 could count those records on macOS 26 but previously could not reliably read or export their media. All personal originals were absent from the optimized local library when counted.

The authoritative personal manifest is `apple-originals/manifests/source-personal-2026-07-12.json` with SHA-256 `793736b9886c1e1c63bdf96d30713205be2576349f68986fe07da102ff353522`.

## Storage Layout

| Path below `apple-originals/` | Purpose | Lifecycle |
|---|---|---|
| `archive/personal/` | Canonical personal originals, rendered edits, AAE files, and XMP/JSON sidecars | Permanent |
| `archive/shared/` | Shared-album media from a separately proven export path | Permanent after acceptance |
| `manifests/` | Source metadata and inventory records | Permanent |
| `reports/` | Export databases, reports, quarantined failures, and reconciliation evidence | Permanent |
| `checksums/` | Portable SHA-256 manifests | Permanent |
| `migration/pilot/` | Representative pilot export | Temporary until final acceptance |
| Future validated import manifest | Every validated original and rendered media rendition selected for Immich | Temporary and removed after import |

The private `apple-originals` SMB share exists only for migration. It authenticates `mbastakis`, maps writes to `apps:apps`, and must be retired after export, reconciliation, backup, and restore acceptance.

The `homeserver-apple-originals-daily` Backrest plan is temporarily retired
while the archive is changing. This avoids backup/export contention and
incomplete migration snapshots; it does not delete existing restic snapshots.
Restore the plan after full export, Immich reconciliation, and restore
acceptance. The independent `homeserver-immich-daily` plan remains active.

## Pilot Evidence

The pilot selected ten personal Photos records covering still images, video, Live Photos, edits, favorites, albums, GPS/no-GPS, and multiple dates. It produced 49 archive files and 17 physical media files. All final archive checksums pass, all 17 media files pass content-type and full-decode validation, all 17 are duplicate-detected by Immich on a repeat dry run, dates and GPS values match the source, both tested Live Photos link correctly, repaired media renders on web and mobile, and the pilot Immich favorite/album/stack metadata pass converges.

The pilot exposed four material behaviors:

1. Traefik's default 60-second whole-request read timeout returned `502 Bad Gateway` for a 133 MB video. The private `websecure` entrypoint now uses a finite three-hour read timeout and ten-minute idle timeout; the same upload then succeeded.
2. Apple Photos intermittently returned an adjustment plist instead of the iCloud original for two edited assets. The files had media extensions but were 933-byte and 1,139-byte XML documents. A fresh retrieval of the same UUIDs returned valid QuickTime and HEIF media. The invalid files remain quarantined under `reports/pilot-invalid-originals/` as evidence.
3. Uploading the complete archive produced two timeline items for a Cinematic video because osxphotos correctly preserved both the unmodified original and rendered edit. This is now accepted: both renditions remain in Immich as well as the archive. Immich cannot attach an arbitrary Apple render to its original as one editable asset, but the pilot API pass shows stacks can group retained renditions with the rendered edit as primary.
4. XMP imported rating, dates, GPS, tags, and descriptions, but the official CLI does not convert Apple favorites or album membership into Immich favorites/albums. The bounded API post-pass handles those fields for the pilot.

## Archive Policy

The canonical archive preserves every available source representation:

- unmodified original media
- rendered edited media
- Live Photo still and motion components
- AAE adjustment recipes
- media-specific `.xmp` and `.json` sidecars
- export database, reports, source manifest, and SHA-256 manifest

No content is accepted based only on its extension. Every expected image/video output must pass a content-type check. XML/plist data under a media extension is quarantined, its source UUID is retried into an isolated directory, and only a validated media file may replace it. A successful osxphotos report is insufficient because its export database compares stat signatures rather than content hashes or media magic.

The full archive export must remain restartable by reusing one Mac-local export database and the same destination/options. Never use `--cleanup`, `--overwrite`, `--ignore-signature`, `--no-exportdb`, conversion options, or embedded ExifTool mutation for the canonical archive.

## Immich Rendition Policy

Immich retains every validated original and rendered media rendition:

| Apple record | Immich timeline representation | Archive representation |
|---|---|---|
| Unedited image/video | Original | Original plus sidecars |
| Edited image/video, including Cinematic mode | Original and rendered edit as separate retained assets | Original, rendered edit, AAE, and sidecars |
| Unedited Live Photo | Original still and paired motion file | Both components plus sidecars |
| Edited Live Photo | Original pair and edited pair when both are valid | Original and edited components, AAE, and sidecars |

The original/edited duplication is intentional preservation, not a migration error. A generated import manifest still controls the upload so invalid media, AAE recipes, JSON reports, and unrelated files cannot become assets. The API metadata pass can use Immich stacks as a presentation layer for each adjusted source record, with the rendered edit as primary and the original still accessible. The official `@immich/cli@3.0.2` remains the upload client, with conservative concurrency and no `--delete`, `--delete-duplicates`, or `--skip-hash` options.

## Metadata API Pass

The source manifest UUID and archive path provide the stable join key; the official CLI's JSON result provides each Immich asset ID. A code-reviewed post-pass through the official Immich API must:

1. Set `isFavorite=true` according to an explicit tested per-rendition policy for the 128 source favorites.
2. Set `visibility="hidden"` for every retained rendition whose Apple source asset is Hidden.
3. Create or reuse the nine regular source albums.
4. Preserve each source album membership across retained renditions according to the tested stack/album behavior.
5. Preserve multi-album membership without duplicating media.
6. Test creating an Immich stack for each adjusted source record, using the rendered edit as primary while retaining the original.
7. Produce a report of source UUID, rendition, Immich asset ID, stack action, favorite action, hidden-visibility action, album actions, and any unresolved record.
8. Be idempotent and support a dry run before mutation.

Do not infer favorites from XMP rating alone. Do not create albums from UUID directory names. Faces and search classifications are regenerated by Immich rather than migrated from Apple's private analysis database.

The live reconcile layer uses Immich's `x-api-key` header from a runtime
environment variable. It can read current favorite state through
`GET /api/assets/{id}` and current stacks through
`GET /api/stacks?primaryAssetId=...` before any mutation. Immich v3.0.2 album
reads do not expose album asset IDs, so album membership cannot be proven
unchanged from a read-only API call; the dry run reports album membership as an
idempotent re-apply action instead of claiming read-verified convergence.

The pilot live reconcile set the planned favorites, created/re-applied the three
planned albums, and converged all four edited-primary stacks. For edited Live
Photos, Immich may omit the paired original motion asset from the stack asset
list and expose it as the still image's `livePhotoVideoId`; the verifier treats
that linked ID as present while still blocking unrelated stack differences.

The current pilot did not include any Apple-hidden source assets. The
plan/reconcile layer now emits and verifies Immich `PUT /api/assets` updates
with `visibility: "hidden"` when `--hidden-policy include` is explicitly selected.
Before any hidden assets are allowed into a bulk import, run and review a hidden
asset dry run, then a bounded apply, against real hidden source assets.

## Policy Decisions And Open Validations

Policy is now settled for hidden assets and shared albums:

- Apple Hidden maps to Immich asset `visibility="hidden"` for every retained original, rendered edit, and Live Photo component associated with a hidden source UUID. Do not map Apple Hidden to Immich Archive or Locked.
- Apple shared albums become ordinary owned Immich albums named from the Apple shared-album names. Do not create Immich shared albums or migrate Apple sharing permissions.

The remaining shared-album blocker is source extraction, not policy. osxphotos
v0.76.1 on macOS 26 could count the 3,857 shared-album records but previously
could not reliably read or export shared-album media. Before any shared-album
import, prove an export path that produces validated media plus album membership
evidence. If osxphotos still fails, use an alternate source path such as Photos
manual export, iCloud export, another macOS version, or an upstream
osxphotos/PhotoScript fix or workaround.

### Hidden Asset Export Gate

On 2026-07-12, a UUID-bounded osxphotos v0.76.1 dry run selected all ten hidden
personal records and predicted 49 archive outputs, including 21 media files,
with no missing or error records. The export directory remained empty during
the dry run. Its report is
`/Volumes/apple-originals/reports/hidden-policy-export-dry-run-2026-07-12.json`
with SHA-256
`9da02077b1fdf9e9a22b80b2d7e23a051cffe942283e255cc42ecfc1c4c6b695`.

The subsequent bounded export used a dedicated destination and export database,
but `--download-missing` stalled in Photos AppleScript automation. osxphotos
reported an AppleScript timeout, terminated Photos, and attempted a retry. The
Photos app entered a failing/unresponsive state and the command was manually
aborted after approximately 20 minutes. The resulting export report is
truncated JSON and is invalid migration evidence; it is retained only as failure
evidence at
`/Volumes/apple-originals/reports/hidden-policy-export-2026-07-12.json`, with
SHA-256
`4ded662aa317532f77f8abfb1a65d37f4f1b020738cfda7b9078937aefdf9d54`.
The dedicated local export database passes SQLite `quick_check` but contains no
completed run, export, or photo records.

The aborted run left 42 of the 49 predicted archive paths and 12 media files
across six source UUIDs. All 12 partial media files pass content-type and full
decode validation, but the set is incomplete and must not be uploaded or treated
as an accepted export. Four source UUIDs have no completed media, accounting for
seven missing predicted paths. The diagnostic report is
`/Volumes/apple-originals/reports/hidden-policy-partial-media-validation-2026-07-12.json`
with SHA-256
`f814d4681857eff218b253a9f51688e73fb0975360be12627198ffd078cef5fb`.

Do not retry the ten-asset `--download-missing` batch. Before any further
automated export, manually confirm Photos opens and the library is healthy. A
future retry must use a fresh isolated destination/report/export database, one
UUID at a time, with an external bounded timeout and a health check between
assets. Preserve this partial directory and truncated report until the failure
has been accepted or superseded by complete evidence.

After Photos was manually confirmed healthy, one-UUID retries successfully
exported two hidden HEIC records and one edited hidden HEIC record into fresh
isolated destinations. The previously stalled hidden video UUID was then tried
alone with a five-minute external timeout; it again failed to complete and was
aborted at the timeout. Photos remained running and no osxphotos process
remained. Treat that video as an explicit source-export blocker; do not extend
the timeout or retry it through the same AppleScript path without a new plan.

The unedited hidden HEIC source UUID
`D73DB796-AB62-45FC-A79E-D862D6CF0039` was selected as the bounded real
hidden-visibility pilot. Its export report is complete, its single 974,075-byte
media file passes content-type and full-decode validation, and its
checksum-bound import manifest contains exactly one original rendition. The
official Immich CLI v3.0.2 dry run found one new asset and zero duplicates, and
the bounded upload created exactly one asset. The reviewed metadata plan
contained only one `set_visibility_hidden` operation. The live read-only
reconcile reported that operation pending, the bounded apply set
`visibility="hidden"`, and the final read-only reconcile reported the operation
unchanged with no errors or warnings. This proves the hidden metadata policy and
implementation against real data, but it does not make the incomplete ten-asset
hidden export acceptable.

No iCloud, Photos-library, archive, or pilot source deletion is authorized before every gate passes and explicit deletion approval is recorded.

## Resume Point

The export content validator, import manifest builder, offline Immich metadata
planner, and live API reconcile command are implemented and pass against the
repaired pilot evidence. The bounded pilot API metadata apply and pilot restore
gates completed. Hidden/shared policy is decided. Do not start the bulk export.
The real hidden-visibility pilot is converged. Next resolve the hidden video
source-export blocker, complete the remaining one-UUID-at-a-time hidden export
evidence, and prove a shared-album export path.
Re-run the pilot checksum and Immich duplicate checks before using the workflow
for all 8,424 personal records.

### Export Validator

Run the read-only validator from the repository root. `REPORT` must be outside
the export tree:

```bash
mise exec -- task infra:photos:validate-export \
  EXPORT_ROOT=/Volumes/apple-originals/migration/pilot/export \
  REPORT=/Volumes/apple-originals/reports/pilot-media-validation-2026-07-12.json
```

The validator treats only known image/video extensions as media candidates,
sniffs XML and binary plist content before invoking external tools, requires
`file(1)` to report the expected image/video MIME class, and performs a full
visual-stream decode with `ffmpeg -xerror`. Its deterministic JSON report lists
every candidate, failure reason, and source UUID requiring isolated retry. A
zero exit status means a non-empty candidate set passed; an empty export or any
validation failure returns exit status 3. The task never belongs in
`infra:validate` because it reads mounted migration data and requires FFmpeg.

The repaired pilot run passed all 17 candidates with no retry UUIDs. Its report
is `/Volumes/apple-originals/reports/pilot-media-validation-2026-07-12.json`
with SHA-256
`85196a551651f3d23681f1e9f2b13dfef6ff3d636d00164148e2b8da90e721fe`.

### Import Manifest

Build the import manifest only from a passing validation report and explicit
source snapshots:

```bash
mise exec -- task infra:photos:build-import-manifest \
  VALIDATION_REPORT=/Volumes/apple-originals/reports/pilot-media-validation-2026-07-12.json \
  SOURCE_MANIFESTS=/Volumes/apple-originals/manifests/source-personal-2026-07-12.json,/Volumes/apple-originals/manifests/source-pilot-supplement-2026-07-12.json \
  OUTPUT=/Volumes/apple-originals/reports/pilot-import-manifest-dry-run-2026-07-12.json
```

The builder fails closed for invalid validation evidence, missing or duplicate
source UUIDs, unavailable media, incomplete source metadata, or an edited
rendition whose source is not adjusted. It includes only validated media,
classifies original and edited image/video renditions, records adjacent XMP
sidecars without treating them as media assets, and binds the validation
report, source manifests, media, and XMP sidecars to SHA-256 hashes. AAE, JSON,
quarantine, and unrelated files never enter the candidate set.

The personal source snapshot was written at 04:13. The edited Live Photo
`2E3AF75F-D9A9-4C59-9599-61C54543EF49` was taken at 04:19 for the pilot, so the
first join correctly failed with that UUID unresolved. A read-only osxphotos
query produced a one-record pilot supplement rather than altering the original
8,424-record snapshot. With both explicit inputs, the dry run passes with 17
entries across ten UUIDs: 12 originals, five edited renditions, 11 images, six
videos, and all four components of the edited Live Photo. No upload was run.

### Immich Metadata Plan

Build the read-only API post-pass plan from the checksum-bound import manifest
and the official Immich CLI upload evidence:

```bash
mise exec -- task infra:photos:plan-immich-metadata \
  IMPORT_MANIFEST=/Volumes/apple-originals/reports/pilot-import-manifest-dry-run-2026-07-12.json \
  UPLOAD_RESULTS="$HOME/Library/Logs/osxphotos/immich-migration/pilot-immich-upload.log" \
  OUTPUT=/Volumes/apple-originals/reports/pilot-immich-metadata-plan-dry-run-2026-07-12.json
```

The planner accepts pure JSON or mixed human/JSON official CLI logs, uses the
latest asset ID for a repeated upload path, records superseded IDs as evidence,
and fails closed for missing asset IDs, upload paths outside the import
manifest, changed source-manifest hashes, malformed source metadata, or hidden
source assets under the default `--hidden-policy block`. With an explicitly
reviewed `--hidden-policy include`, the plan emits `PUT /api/assets` updates
with `visibility: "hidden"` for each hidden binding. The plan emits the exact
client-side dry-run protocol for Immich v3.0.2: look up albums before creating
them, add retained renditions to albums, set favorites and hidden visibility
with `PUT /api/assets`, and prepare edited-primary stack payloads with
`POST /api/stacks` only after a future `GET /api/stacks?primaryAssetId=...`
check.

The pilot metadata plan passes with 17 asset bindings, two favorite asset
updates for the favorite Live Photo components, three album ensure operations
(`Progress`, `Instagram`, and `Immich Migration Pilot`), and four edited-primary
stack plans. The only warning is expected: two upload-log asset IDs were
superseded by the repaired invalid-original retry, and the latest IDs are used.
No Immich API key was created and no API request was sent. The plan is
`/Volumes/apple-originals/reports/pilot-immich-metadata-plan-dry-run-2026-07-12.json`
with SHA-256
`1e481df9915d61153d8894bf817b7c13a1dd08f43514c89a620dd8799cdf3370`.

### Immich Metadata Reconcile

Run the live API comparison only after creating a short-lived Immich API key in
the web UI and exporting it into the current shell without writing it to disk:

```bash
mise exec -- task infra:photos:reconcile-immich-metadata \
  METADATA_PLAN=/Volumes/apple-originals/reports/pilot-immich-metadata-plan-dry-run-2026-07-12.json \
  OUTPUT=/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-dry-run-2026-07-12.json
```

The task reads `IMMICH_API_KEY` by default and never accepts the key as a command
argument. Without `APPLY=true`, it performs only API reads and writes a report of
favorite, hidden-visibility, album, and stack operations. Exit code `2` means the dry run found
pending safe mutations, `3` means the reviewed plan or live state is blocked,
and `0` means no pending operation remains. Mutation requires an explicit
`APPLY=true` task variable and must only be used after reviewing the dry-run
report. Revoke the temporary API key immediately after the bounded operation.

The first live dry run found only expected pending safe mutations: two favorite
updates, three album ensures, and four edited-primary stack creates. Its report
is `/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-dry-run-2026-07-12.json`
with SHA-256
`19c977cab7c08b67e6100e64a9dede3455943f2c2f9b9a0dd9a6231f2508a834`.

The first bounded apply created/re-applied the planned favorites and albums and
created three stacks, then blocked on `stack_create_unverified` for the edited
Live Photo because Immich returned the original motion component as
`livePhotoVideoId` rather than as a direct stack asset. The diagnostic report is
`/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-apply-2026-07-12.json`
with SHA-256
`d76bc7705f39db932c1edd4f9d3d602ba2e7f355ef6ffa102c76bff7a6f945f1`.

After updating the verifier for that Immich Live Photo shape, the post-fix
read-only report has no errors: favorites and all four stacks are unchanged,
while albums remain pending only because Immich v3.0.2 cannot expose membership
for read verification. Its report is
`/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-post-fix-dry-run-2026-07-12.json`
with SHA-256
`213ca98e9ac9217be1954abf1c6eddc73d0d0e6abfde391c7f4dfd8e213d0f39`.
The final bounded `APPLY=true` pass is valid with no errors: album membership is
idempotently re-applied and favorites/stacks are unchanged. Its report is
`/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-apply-post-fix-2026-07-12.json`
with SHA-256
`875701e4f912b696f9855247d10bab75f84f270db5f77488c748e8f304e1af1c`.

### Pilot Restore Gates

The local ZFS restore gate used the
`pool_4tb/homeserver/data/photos/apple-originals@auto-2026-07-12_06-00`
snapshot, restored `/migration/pilot/export` into an isolated TrueNAS `/tmp`
directory, and verified all 49 entries in
`/Volumes/apple-originals/checksums/pilot-export-2026-07-12.sha256` with
`sha256sum -c`. The temporary restore directory was removed after verification.

The Backrest/restic Apple-originals gate first created manual snapshot
`da402ba4` for `/source/apple-originals` with tags
`plan:homeserver-apple-originals-daily`, `created-by:truenas`, and
`manual:apple-photos-pilot-restore-test`. It restored the pilot export path from
S3 into an isolated Backrest-container `/tmp` directory and verified all 49 pilot
checksum entries. The temporary restore directory was removed after
verification.

The Backrest/restic Immich-media gate created manual snapshot `d19791c5` for
`/source/immich` with tags `plan:homeserver-immich-daily`,
`created-by:truenas`, and `manual:apple-photos-pilot-restore-test`. It restored
that snapshot into an isolated Backrest-container `/tmp` directory and compared
the restored file checksum tree against live `/source/immich`. The temporary
restore and checksum files were removed after verification.

The Immich logical database restore gate dumped the live `immich` PostgreSQL
database with `pg_dump -Fc`, producing temporary dump SHA-256
`372a2208768af3d3be883ebf64977e33b433ff15c15925d9d35fa2d9da565e2b` and size
18 MB on Atlas. It restored successfully into a disposable container using the
same Immich PostgreSQL image. Restored counts matched live counts: 18 assets,
three albums, six album assets, four stacks, one user, and 85 migrations. The
temporary dump and disposable container were removed after verification.

## Next-Agent Handoff

This is the authoritative handoff after the 2026-07-12 pilot. The repository has broader pre-existing uncommitted infrastructure reorganization; do not revert or rewrite unrelated changes.

### Live State

- Immich v3.0.2 is healthy at `https://photos.mbastakis.com` with working Authentik login, web access, mobile access, uploads, GPS, XMP metadata, and Live Photos.
- The temporary `apple-originals` SMB share is active, code-managed, zero-drift, and mounted on the Mac at `/Volumes/apple-originals`. It has about 3.3 TiB available.
- Traefik is running with `websecure` request read timeout `3h` and idle timeout `10m`. The previously failing 133 MB pilot video succeeds through the proxy.
- The ten-record pilot remains in Immich. Its original/edited Cinematic pair intentionally remains duplicated under the accepted rendition-preservation policy; do not manually delete either item. The live API metadata pass converged favorites, albums, and edited-primary stacks for the pilot.
- Two invalid pilot uploads were permanently removed through the official API and replaced with validated media. The archive retains the bad XML files only under `reports/pilot-invalid-originals/` as evidence.
- The short-lived pilot Immich API key was revoked in the Immich web UI after the bounded reconcile. The macOS clipboard was cleared after use. No migration API key is stored in BWS or on disk.
- One validated hidden HEIC was uploaded as a bounded policy pilot and converged to Immich `visibility="hidden"`; the final read-only reconcile reports it unchanged.
- The short-lived API key used for the hidden policy pilot was revoked in the Immich web UI. The macOS clipboard was cleared after the operation; the key was not written to BWS, disk, CLI logs, or Git.
- Pilot restore gates passed: local ZFS restored the repaired archive, Backrest/restic restored both Apple originals and Immich media from S3, and an Immich logical dump restored into disposable PostgreSQL.
- Full personal-library export, shared-album export, bulk Immich import, source deletion, and iCloud deletion have not started.

### Durable Evidence

| Evidence | Location or value |
|---|---|
| Personal source manifest | `/Volumes/apple-originals/manifests/source-personal-2026-07-12.json` |
| Source manifest SHA-256 | `793736b9886c1e1c63bdf96d30713205be2576349f68986fe07da102ff353522` |
| Pilot export | `/Volumes/apple-originals/migration/pilot/export/` |
| Current pilot checksum manifest | `/Volumes/apple-originals/checksums/pilot-export-2026-07-12.sha256` |
| Pre-repair checksum manifest | `/Volumes/apple-originals/reports/pilot-export-before-original-repair.sha256` |
| Pilot osxphotos report/database | `/Volumes/apple-originals/reports/pilot-export-2026-07-12.{json,db}` |
| Quarantined false originals | `/Volumes/apple-originals/reports/pilot-invalid-originals/` |
| Pilot media validation report | `/Volumes/apple-originals/reports/pilot-media-validation-2026-07-12.json` |
| Pilot media validation SHA-256 | `85196a551651f3d23681f1e9f2b13dfef6ff3d636d00164148e2b8da90e721fe` |
| Pilot source supplement | `/Volumes/apple-originals/manifests/source-pilot-supplement-2026-07-12.json` |
| Pilot source supplement SHA-256 | `11d5c0c41e2b872cd486635991eb31aa5d99bc4a34637a8ebb23a96b09c0fbeb` |
| Pilot import-manifest dry run | `/Volumes/apple-originals/reports/pilot-import-manifest-dry-run-2026-07-12.json` |
| Pilot import-manifest SHA-256 | `b87b1b994f7df045b81df66f83d298b971b2466c9de4369fd8f65ca1723eb795` |
| Pilot Immich metadata-plan dry run | `/Volumes/apple-originals/reports/pilot-immich-metadata-plan-dry-run-2026-07-12.json` |
| Pilot Immich metadata-plan SHA-256 | `1e481df9915d61153d8894bf817b7c13a1dd08f43514c89a620dd8799cdf3370` |
| Pilot Immich metadata reconcile dry run | `/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-dry-run-2026-07-12.json` |
| Pilot Immich metadata reconcile dry-run SHA-256 | `19c977cab7c08b67e6100e64a9dede3455943f2c2f9b9a0dd9a6231f2508a834` |
| Pilot Immich metadata reconcile apply diagnostic | `/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-apply-2026-07-12.json` |
| Pilot Immich metadata reconcile apply diagnostic SHA-256 | `d76bc7705f39db932c1edd4f9d3d602ba2e7f355ef6ffa102c76bff7a6f945f1` |
| Pilot Immich metadata reconcile post-fix dry run | `/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-post-fix-dry-run-2026-07-12.json` |
| Pilot Immich metadata reconcile post-fix dry-run SHA-256 | `213ca98e9ac9217be1954abf1c6eddc73d0d0e6abfde391c7f4dfd8e213d0f39` |
| Pilot Immich metadata reconcile final apply | `/Volumes/apple-originals/reports/pilot-immich-metadata-reconcile-apply-post-fix-2026-07-12.json` |
| Pilot Immich metadata reconcile final apply SHA-256 | `875701e4f912b696f9855247d10bab75f84f270db5f77488c748e8f304e1af1c` |
| Hidden policy pilot export report | `/Volumes/apple-originals/reports/hidden-policy-export-D73DB796-AB62-45FC-A79E-D862D6CF0039-2026-07-12.json` |
| Hidden policy pilot export report SHA-256 | `a2be6823d76a590709a410724952afeaea079138d53e253f2bba276ae6f9b3dd` |
| Hidden policy pilot media validation | `/Volumes/apple-originals/reports/hidden-policy-D73DB796-media-validation-2026-07-12.json` |
| Hidden policy pilot media validation SHA-256 | `e71582802cdfbfe7bfab8e3d86929046a601156802c3bafec83f5197fabe00cd` |
| Hidden policy pilot import manifest | `/Volumes/apple-originals/reports/hidden-policy-D73DB796-import-manifest-2026-07-12.json` |
| Hidden policy pilot import manifest SHA-256 | `a6787e4a52fbb53a063c5d294899da35f57d0d5507a4c19ea70709e610938915` |
| Hidden policy pilot Immich metadata plan | `/Volumes/apple-originals/reports/hidden-policy-D73DB796-immich-metadata-plan-2026-07-12.json` |
| Hidden policy pilot Immich metadata plan SHA-256 | `a12140feb1317c45be46ad1879ebe44f351f2255f741f405cfe783efdd9c431b` |
| Hidden policy pilot reconcile dry run SHA-256 | `326f965f53d047a2173a64a21f86269e82688c5dc9bc4950c2f427fe6f8d0ac6` |
| Hidden policy pilot reconcile apply SHA-256 | `c005a91beca1f818e56d72884370d56b7178ce8ffd7ffffdd5056ebca9e6bc32` |
| Hidden policy pilot post-apply reconcile SHA-256 | `f3212613196d7107b43d879c8a9aaa0c54f37ee91ffbc54ed621f5912ad040df` |
| Hidden policy pilot official CLI dry-run log SHA-256 | `8af61e0b0eeb44dbd57b1e67bdfaeba5dcb3388dd5238c14c9bca531770d9883` |
| Hidden policy pilot official CLI upload log SHA-256 | `8c8b7779b8f34e8566194ecc15264de20fad713b50d7c1a587cd38695c4f868a` |
| ZFS pilot restore source | `pool_4tb/homeserver/data/photos/apple-originals@auto-2026-07-12_06-00` |
| Apple-originals restic pilot snapshot | `da402ba4` (`/source/apple-originals`, 278.348 MiB) |
| Immich-media restic pilot snapshot | `d19791c5` (`/source/immich`, 244.232 MiB) |
| Immich logical dump restore SHA-256 | `372a2208768af3d3be883ebf64977e33b433ff15c15925d9d35fa2d9da565e2b` |
| Immich logical dump restored counts | `assets=18`, `albums=3`, `album_assets=6`, `stacks=4`, `users=1`, `migrations=85` |
| Local resumable pilot export DB | `~/Library/Application Support/osxphotos/immich-migration/pilot.db` |
| Local Immich CLI pilot log | `~/Library/Logs/osxphotos/immich-migration/pilot-immich-upload.log` |

The current checksum manifest has 49 entries and was verified after replacing both invalid originals. A repeat official CLI dry run reported zero new files and 17 duplicates.

### Ordered Resume Plan

1. Completed 2026-07-12: implement a read-only export validator that rejects XML/plist content under media extensions, verifies image/video decodability, emits source UUIDs requiring retry, and never trusts the osxphotos success count alone.
2. Completed 2026-07-12: run that validator against the existing pilot and add sanitized fixture tests for the two quarantined plist behaviors without committing personal media.
3. Completed 2026-07-12: implement and run a checksum-bound dry-run import manifest builder that includes every validated original and rendered rendition for each source UUID while excluding AAE, JSON, quarantined, and invalid files.
4. Completed 2026-07-12: reconcile the pilot upload log to all 17 validated Immich asset IDs and generate the reviewed favorite, album, and edited-primary stack API plan.
5. Completed 2026-07-12: document and implement that Apple Hidden maps to Immich `visibility="hidden"`, then prove the plan, live dry run, bounded apply, and post-apply convergence against one validated real hidden HEIC. The ten-asset hidden export remains incomplete: three one-UUID retries succeeded, while the hidden video timed out alone after five minutes. Remaining work: resolve that source-export blocker and complete isolated evidence for all ten records before bulk import.
6. Completed 2026-07-12: document that Apple shared albums become owned Immich albums, not Immich shared albums. Remaining work: prove a shared-album export path because osxphotos v0.76.1 on macOS 26 can count but cannot yet reliably read/export the 3,857 shared records.
7. Completed 2026-07-12: run the live execution layer for the idempotent official API metadata post-pass against the pilot, including the Live Photo stack verifier fix.
8. Completed 2026-07-12: revoke the short-lived Immich API key created for the pilot reconcile. The clipboard was cleared after use; no key was written to BWS, disk, or Git.
9. Completed 2026-07-12: execute isolated ZFS, Backrest/restic, and logical database-dump restore tests for the repaired pilot, including both Apple-originals and Immich-media offsite snapshots.
10. Re-run repository validation, SMB/Atlas plans, pilot SHA-256 verification, media validation, and Immich duplicate detection.
11. Present the validator, rendition/stack, metadata, hidden/shared, restore, refreshed capacity, and cost results for explicit go/no-go approval.
12. Start the full personal archive export only after approval. Bulk import is a later separately approved operation.

### Prohibited Shortcuts

- Do not drop a valid unmodified original or rendered edit to suppress duplicates; both are accepted Immich assets.
- Do not upload the archive tree indiscriminately; use the validated import manifest so AAE, JSON, quarantined, and invalid files remain outside Immich.
- Do not enable `Download Originals to this Mac`; the approximately 203.7 GB source exceeds safe local staging capacity.
- Do not trust extensions, osxphotos report success, export DB signatures, or file size alone as proof of valid media.
- Do not treat the osxphotos shared-album record count as proof that shared-album media or membership has been exported.
- Do not retry the failed ten-hidden-asset `--download-missing` batch or upload any file from its incomplete partial export.
- Do not use osxphotos `--cleanup`, `--overwrite`, `--ignore-signature`, `--no-exportdb`, media conversion, or embedded ExifTool mutation for the canonical archive.
- Do not use Immich CLI `--delete`, `--delete-duplicates`, or `--skip-hash`.
- Do not write directly into Immich-managed storage or database tables; use the official CLI/API.
- Do not map Apple Hidden to Immich Archive or Locked, and do not create Immich shared albums from Apple shared albums.
- Do not preserve a migration API key in BWS, shell history, logs, repository files, or chat.
- Do not remove the SMB share, pilot evidence, iCloud data, or Photos library until migration and restore acceptance is explicit.

### Validation At Handoff

- `mise exec -- task infra:validate` passes with 78 tests.
- Targeted pre-commit hooks pass, including Gitleaks.
- `mise exec -- task truenas:smb:plan` reports the share and service unchanged.
- Atlas homeserver syntax validation passes, the timeout configuration is applied, and the post-apply plan is clean except for the existing check-mode-only Homepage background-image prediction.
- `git diff --check` passes.

## References

- [Immich architecture decision](../adr/0005-run-immich-on-atlas-with-truenas-storage.md)
- [osxphotos issue 1381: adjustment plist exported as original media](https://github.com/RhetTbull/osxphotos/issues/1381)
- [PhotoScript issue 47](https://github.com/RhetTbull/PhotoScript/issues/47)
- [Immich v3.0.2 reverse proxy guidance](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/docs/docs/administration/reverse-proxy.md)
- [Immich v3.0.2 XMP sidecars](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/docs/docs/features/xmp-sidecars.md)
- [Immich v3.0.2 OpenAPI spec](https://github.com/immich-app/immich/blob/443b856ac3914dd5edc1a10827664c5b1a0abf76/open-api/immich-openapi-specs.json)
