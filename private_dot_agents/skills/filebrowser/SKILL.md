---
name: filebrowser
description: Manage files.mbastakis.com through the `homeserver_personal:` and `homeserver_household:` rclone WebDAV remotes. Use when the user asks to list, find, download, upload, organize, rename, move, or remove homeserver files, or refers to FileBrowser, Personal files, Household files, or the homeserver files drive.
---

# FileBrowser

Use FileBrowser Quantum WebDAV through two explicit `rclone` remotes:

- `homeserver_personal:` — Michail's complete private Personal source.
- `homeserver_household:` — the shared Household source.

Both use Tailscale-only HTTPS and Michail's FileBrowser identity. Neither remote exposes Chara's private Personal area.

The discipline is _reversible_: select the correct area, inspect exact paths, preview mutations, execute the smallest operation, then verify both sides.

## Workflow

1. **Preflight** — confirm `rclone` exists; confirm `RCLONE_CONFIG_HOMESERVER_PERSONAL_PASS` and `RCLONE_CONFIG_HOMESERVER_HOUSEHOLD_PASS` are set without printing them; run `rclone lsd` against the requested remote. _Done when the selected area is reachable and no credential value has appeared in output._
2. **Inspect** — select Personal or Household from the user's context, then list the narrowest relevant path with `lsjson`, `lsf`, or `lsd`. If the area is ambiguous, inspect both read-only or ask before writing. Quote every path. _Done when every source and destination is identified exactly, including whether the destination exists._
3. **Preview** — add `--dry-run` to uploads, copies, moves, renames, and trash operations. Show the source and destination before an ambiguous, recursive, overwriting, cross-area, or destructive mutation. _Done when the preview changes only the intended paths._
4. **Mutate** — use the narrowest command below. Never use `sync`, `bisync`, `delete`, `deletefile`, `purge`, `rmdir`, `rmdirs`, `cleanup`, or `dedupe`. Never overwrite without explicit approval. _Done when the command succeeds without broadening scope._
5. **Verify** — re-list the exact remote paths. For uploads, download the result to a temporary directory and compare local SHA-256 hashes because generic WebDAV does not expose reliable server hashes. _Done when remote state matches the request and uploaded bytes hash-identically._

## Commands

```bash
# Browse each root
rclone lsd 'homeserver_personal:'
rclone lsd 'homeserver_household:'
rclone lsjson 'homeserver_personal:Documents/Health' --max-depth 1
rclone lsf 'homeserver_household:Shared Documents' --max-depth 2

# Download one file into an existing local directory
rclone copy 'homeserver_personal:Documents/Health/report.pdf' '/local/directory'

# Upload one file without replacing an existing file
rclone copyto '/local/report.pdf' \
  'homeserver_personal:Documents/Health/report.pdf' --immutable

# Create a directory
rclone mkdir 'homeserver_household:Shared Documents/New Folder'

# Rename or move one remote item
rclone moveto 'homeserver_personal:old/path.pdf' \
  'homeserver_personal:new/path.pdf'

# Reversible removal within the same area
rclone moveto 'homeserver_personal:Documents/old.pdf' \
  'homeserver_personal:Trash/YYYY-MM-DD/Documents/old.pdf'
rclone moveto 'homeserver_household:Shared Documents/old.pdf' \
  'homeserver_household:Trash/YYYY-MM-DD/Shared Documents/old.pdf'
```

Use `copyto` for a single named upload and `moveto` for a single rename or move. Use `copy` only when the destination is a directory. Add `--immutable` to uploads unless replacement is explicitly approved.

## Safety Boundary

- Keep private Michail material in Personal and genuinely shared household material in Household. Do not move content between these areas without explicit approval.
- Treat Files as authoritative for original documents. Obsidian receives summaries and links, not copied originals, unless the user changes that policy.
- Treat PDFs and document scans as documents, not Photos. To inspect a PDF, run `pdftotext -layout input.pdf output.txt` and read only the text output.
- Do not print, log, inspect, or transmit either rclone password environment variable.
- Do not place credentials in commands, `rclone.conf`, files, prompts, or Git.
- Do not use raw SSH, SMB, NFS, or TrueNAS dataset paths for normal file operations.
- Never permanently delete. Move unwanted content to `Trash/YYYY-MM-DD/<original path>` within the same remote; emptying Trash is manual.
- Require explicit confirmation before recursive moves, replacement, moving more than one item, cross-area operations, or moving anything to Trash.
- Preserve local sources until upload verification succeeds. Do not use flags that delete local files.

## Troubleshooting

- `401 Unauthorized`: the API token is missing, expired, revoked, customized, or the user lacks API permission.
- `403 Forbidden`: Michail lacks the required permission on the selected FileBrowser source or the path is outside its scope.
- Missing remotes: verify `~/.config/rclone/rclone.conf` contains `[homeserver_personal]` and `[homeserver_household]`.
- Browser works but WebDAV fails: confirm the URLs are `https://files.mbastakis.com/dav/Personal/` and `https://files.mbastakis.com/dav/Household/`, and WebDAV remains enabled in Kavouki.
