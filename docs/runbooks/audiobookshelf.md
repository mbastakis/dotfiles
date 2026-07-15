# Audiobookshelf

Audiobookshelf runs as a pinned TrueNAS community catalog app and is reached privately at `https://audiobooks.mbastakis.com/audiobookshelf/` through Atlas Traefik. The hostname root redirects to that canonical path. It supports mobile audiobook playback/downloads and ebook reading. Audiobookshelf does not currently provide integrated ebook text-to-speech; use a separate mobile reader or import externally generated audio when TTS is needed.

## Storage

| Dataset | Container path | Access | Purpose |
|---|---|---|---|
| `pool_4tb/homeserver/apps/audiobookshelf/config` | `/config` | read/write | SQLite database, users, settings, and progress |
| `pool_4tb/homeserver/apps/audiobookshelf/metadata` | `/metadata` | read/write | Covers, metadata, cache, logs, and temporary streams |
| `pool_4tb/homeserver/apps/audiobookshelf/backups` | `/backups` | read/write | Application-consistent backup archives |
| `pool_4tb/homeserver/data/books` | `/books` | read-only | Audiobooks and DRM-free ebooks |

Keep related formats together so one item can provide both reading and listening:

```text
/books/Author/Book/
|-- Book.m4b
|-- Book.epub
`-- cover.jpg
```

The read-only library prevents an application compromise or mistaken UI action from changing media. A standalone EPUB at the library root is one book item, so flat EPUB imports are supported. Keep audio, multiple formats, or sidecar files in one leaf directory per book. Import as an operator, then scan the library:

```bash
invalid=0
for book in ./books/*.epub; do
    unzip -tq "$book" >/dev/null 2>&1 || invalid=$((invalid + 1))
done
test "$invalid" -eq 0

rsync -rtv --rsync-path="sudo -u apps rsync" ./books/ truenas:/mnt/pool_4tb/homeserver/data/books/
```

Validate EPUB ZIP containers before transfer. Run the receiver as the TrueNAS `apps` user and do not use archive mode. `rsync -a` preserves workstation ownership and permissions; files that are not world-readable can then be indexed but cannot be opened by the Audiobookshelf container.

## Deploy

Review every plan before its matching apply:

```bash
mise exec -- task truenas:tofu:plan
mise exec -- task truenas:tofu:apply

mise exec -- task truenas:apps:plan -- audiobookshelf
mise exec -- task truenas:apps:apply -- audiobookshelf

mise exec -- task identity:authentik:plan
mise exec -- task identity:authentik:apply

mise exec -- task truenas:audiobookshelf:plan
mise exec -- task truenas:audiobookshelf:apply

mise exec -- task aws:dns:plan
mise exec -- task aws:dns:apply

mise exec -- task atlas:audiobookshelf:plan
mise exec -- task atlas:audiobookshelf:apply

mise exec -- task truenas:snapshots:audiobookshelf:plan
mise exec -- task truenas:snapshots:audiobookshelf:apply
mise exec -- task truenas:snapshots:books:plan
mise exec -- task truenas:snapshots:books:apply

mise exec -- task truenas:backrest:plan
mise exec -- task truenas:backrest:apply
```

## First Start

`truenas:audiobookshelf:apply` uses Audiobookshelf's supported APIs to create the `michail` root user, create the Book library at `/books`, configure stable server and scanner settings, configure the Sunday 02:00 built-in backup with eight retained archives, and configure native Authentik OIDC. The root password and OIDC client secret are resolved from BWS and never stored in Git or plan output.

The managed profile keeps covers and metadata in `/metadata` because `/books` is read-only, permits ebook-only items, blocks EPUB scripted content, uses local/embedded covers without automatic external lookups, watches the local library for changes, sorts without leading English articles, and keeps iframe embedding and cross-origin browser access disabled. Display settings use detail view, `dd/MM/yyyy`, 24-hour time, and English. Library scans, item metadata edits, users, sessions, API keys, feeds, and statistics remain runtime state rather than desired configuration.

1. Open `https://audiobooks.mbastakis.com/audiobookshelf/` from a Tailscale-connected device and complete the first Authentik login as `michail`. Username matching links that Authentik subject to the existing Audiobookshelf root record.
2. Install the official Audiobookshelf mobile app, connect it to `https://audiobooks.mbastakis.com`, choose Authentik, and test streaming plus an offline download before importing the full library.
3. Confirm newly authorized household users auto-register with the `user` role; only the managed `michail` identity receives the `admin` claim and may link to the root user.

The targeted Atlas task installs only the Traefik route. The Homepage card is rendered by the full `atlas:homeserver:apply` workflow and may be deployed later with other reviewed dashboard changes.

Audiobookshelf 2.35.1 requires its compiled `/audiobookshelf` router prefix for reliable web callback validation. Authentik registers strict web and mobile redirects:

```text
https://audiobooks.mbastakis.com/audiobookshelf/auth/openid/callback
https://audiobooks.mbastakis.com/audiobookshelf/auth/openid/mobile-redirect
```

OIDC auto-launch puts Authentik in the normal web login path. Local authentication stays enabled for reconciliation and break-glass recovery; bypass auto-launch at `https://audiobooks.mbastakis.com/audiobookshelf/login?autoLaunch=0` and use the BWS-backed `audiobookshelf_root_password` only when OIDC is unavailable. Traefik forward-auth is intentionally not used because it would interfere with native mobile/API authentication.

The bounded API desired state is `infra/truenas/audiobookshelf/audiobookshelf.yaml`. Run a second `truenas:audiobookshelf:plan` after changes; it should report the root user, server settings, library, backup policy, and OpenID settings as unchanged.

## Protection

| Layer | Schedule | Retention |
|---|---|---|
| Audiobookshelf built-in archive | Sunday 02:00 | 8 archives |
| Audiobookshelf app-state ZFS snapshot | Sunday 03:00 and monthly day 1 at 03:15 | 8 weekly, 12 monthly |
| Audiobookshelf archive Backrest plan | Sunday 03:30 | 8 weekly, 12 monthly |
| Books ZFS snapshot | Monthly day 1 at 04:00 | 12 monthly |
| Books Backrest plan | Monthly day 1 at 04:30 | 6 monthly, 3 yearly |

The accepted recovery-point window is up to seven days of progress and settings changes, and up to one month of newly imported books. Run the two Backrest plans manually after a major import when that media loss window is unacceptable.

## Restore

Restore media and application state separately:

1. Stop Audiobookshelf before restoring filesystem state.
2. Restore `/books` from Backrest or a ZFS snapshot without changing its container path.
3. Prefer Audiobookshelf's built-in restore action for an archive from `/backups`.
4. For a full ZFS rollback, restore the app parent recursively so `/config`, `/metadata`, and `/backups` come from one recovery point.
5. Start the app, verify the library paths, and test one user's progress before allowing normal use.

Do not restore only a live SQLite file while the app is running. Built-in archives do not contain audiobook or ebook media.
