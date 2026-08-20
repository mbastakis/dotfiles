# Email (NeoMutt Gmail Stack)

Terminal Gmail stack managed by chezmoi: `NeoMutt` + `mbsync` + `msmtp` + `notmuch` + `abook`. Accounts are rendered from `.chezmoidata.yaml` (`mail.accounts`); a launchd LaunchAgent syncs in the background.

Keybindings are documented in [shortcuts.md](shortcuts.md#neomutt) — not here.

## Architecture

| Layer | Tool | Purpose | Managed Path |
|---|---|---|---|
| Sync | `mbsync` (`isync`) | IMAP sync into Maildir | `~/.config/isyncrc` |
| Send | `msmtp` | SMTP send via Gmail | `~/.config/msmtp/config` |
| Index/Search | `notmuch` | Unified inbox + fast search + tags | `~/.config/notmuch/default/config` |
| Client | `NeoMutt` | Mail UI, mailbox views, compose flow | `~/.config/neomutt/` |
| Contacts | `abook` | Local contact store + completion | `~/.config/abook/abookrc`, `~/.local/share/abook/addressbook` |
| Orchestration | `mail-sync` | Locking, logging, mbsync → notmuch pipeline | `~/bin/mail-sync` |
| Scheduling | launchd LaunchAgent | `mail-sync --quiet` at login + every `sync_interval_minutes` | `~/Library/LaunchAgents/com.mbastakis.mail-sync.plist` |

## Why App Passwords

- One Gmail app password per account covers both IMAP and SMTP.
- Simpler to set up and maintain than personal OAuth2 consent/token management; revisit OAuth2 only if Google withdraws app passwords.
- Passwords are pulled from Bitwarden Secrets at `chezmoi apply` time (`bitwardenSecrets` template function) and baked into the rendered `isyncrc` and msmtp config — there is no runtime password command.

## First-Time Setup

1. Enable 2-Step Verification for each Gmail account and create one app password per account (not blocked by Advanced Protection or org policy).
2. Store each app password as a Bitwarden secret; record its UUID in `.chezmoidata.yaml` under `mail.accounts[].secrets.app_password_uuid`.
3. Ensure BWS auth works: `bws` CLI is installed by `.chezmoiscripts/run_onchange_before_01-install-bws.sh`, and `BWS_ACCESS_TOKEN` is exported from `~/.local/share/bws/token` (see `dot_zshenv.tmpl`).
4. In Gmail web settings, keep IMAP enabled and the required folders visible (`INBOX`, `[Gmail]/Sent Mail`, `[Gmail]/Drafts`, `[Gmail]/Spam`, `[Gmail]/Trash`).
5. Apply and validate:

```bash
chezmoi apply                    # renders configs, creates runtime dirs, places the LaunchAgent plist
mail-sync --dry-run              # mbsync dry run, skips notmuch indexing
neomutt -n -F "$HOME/.config/neomutt/neomuttrc" -D   # config parses cleanly
```

6. The LaunchAgent plist is placed by `chezmoi apply` and loads at next login (`RunAtLoad`). To start it immediately:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mbastakis.mail-sync.plist
```

Notes:

- The first full sync can take a long time; `sync_all_mail: true` pulls `[Gmail]/All Mail` and can be very large.
- `UIDVALIDITY` notices during first mailbox initialization are expected.
- Runtime directories (Maildir root, notmuch DB, isync state, logs, hook dir) are created by `.chezmoiscripts/run_onchange_after_07-mail-runtime-dirs.sh.tmpl`.

## Daily Workflow

Aliases (from `private_dot_config/zsh/aliases.zsh`): `nm` opens NeoMutt, `msync` runs `mail-sync`, `ab` opens abook.

```bash
mail-sync                        # sync all accounts, then notmuch new + post-sync hooks
mail-sync --account mbastakis    # sync a single account/channel
mail-sync --dry-run              # preview without touching the index
notmuch search 'tag:inbox and not tag:spam and not tag:trash'   # what the unified inbox shows
```

`mail-sync` takes a lock (`~/.local/state/mail/mail-sync.lock`), logs to `~/.local/state/mail/log/mail-sync.log`, and after a successful real sync runs any executables in `~/.config/mail/hooks/post-sync.d/` (failures are logged as warnings, never fail the sync).

## NeoMutt Mailbox Workflow

- The unified inbox is a notmuch virtual mailbox over all accounts: `tag:inbox and not tag:spam and not tag:trash`. `virtual_spool_file=yes` makes it the startup mailbox.
- The notmuch `post-new` hook tags every message with `acct-<id>` plus role tags (`inbox`, `sent`, `draft`, `spam`, `trash`) derived from its Maildir path.
- Per-account sent/drafts/spam/trash views are virtual mailboxes over those tags (`tag:acct-<id> and tag:sent`, ...); per-account inboxes appear once in the sidebar as numbered physical Maildir rows matching the `i1`..`i9` jump macros.
- Folder hooks in `accounts.muttrc.tmpl` switch identity and `sendmail="msmtp --account=<id>"` per account, and rebind the role-jump macros (`gi`/`gs`/`gd`/`gp`/`gt`) and per-account sync (`gr`) to the current account.
- `set record=""` disables local sent copies — Gmail already stores sent mail, so this avoids duplicates.
- Noisy backend tags (account/role tags) are hidden in the index; attachment and user labels stay visible.

## NeoMutt Tuning

Each option below exists in `private_dot_config/neomutt/base.muttrc` (or `neomuttrc.tmpl`) for a reason:

- `pager_read_delay=1` — a briefly previewed message is not marked read.
- `pager_stop=yes` — `PageDown` stays inside the current mail instead of auto-advancing.
- `use_threads=threads` — thread display is decoupled from sort order, so the index threads while sorting by recent activity.
- `reply_with_xorig=yes` — replies pick the delivered alias when `X-Original-To` is present.
- `abort_noattach=ask-yes` — warns when the body mentions an attachment but none is attached.
- `header_cache_compress_method="zlib"` level 1 — smaller header cache at negligible CPU cost.
- `read_inc=1000` / `write_inc=1000` / `time_inc=500` — fewer progress redraws on large folders.
- `query_command` points abook at explicit config/datafile paths so completion works regardless of cwd/env.
- Wide sidebar (42 cols) with `unread/total` counts; Catppuccin-style 256-color palette for reliable rendering inside `tmux-256color`; mailcap opens images/PDFs via `/usr/bin/open`.

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing tool/config/path errors | `chezmoi apply --dry-run --force`, then `neomutt -n -F "$HOME/.config/neomutt/neomuttrc" -D` |
| IMAP auth failures | Recreate the Gmail app password, update the Bitwarden secret, then **re-run `chezmoi apply`** — passwords are baked into rendered configs at apply time |
| `bitwardenSecrets` errors during apply | Verify `bws` is on PATH and `BWS_ACCESS_TOKEN` is set (sourced from `~/.local/share/bws/token`) |
| SMTP failures | `msmtp --serverinfo --account=<id>` |
| Unified inbox empty/stale | Run `mail-sync`; verify `notmuch config list` and `notmuch new` |
| `notmuch new` prints `.uidvalidity` notices | Safe Maildir metadata; `new.ignore=.uidvalidity` in the notmuch config suppresses it |
| Background sync not running | `plutil -lint ~/Library/LaunchAgents/com.mbastakis.mail-sync.plist`; `launchctl print gui/$(id -u)/com.mbastakis.mail-sync`; check `~/.local/state/mail/log/launchd-mail-sync.{out,err}.log` |
| Sync appears stuck | Check `~/.local/state/mail/log/mail-sync.log`; a stale lock at `~/.local/state/mail/mail-sync.lock` is auto-cleared when the recorded PID is dead |
| Contacts completion mismatch | Ensure `~/.config/abook/abookrc` and `~/.local/share/abook/addressbook` exist and `query_command` still names both paths |

## Gmail Caveats

- `[Gmail]/All Mail` sync (`sync_all_mail`, currently enabled per account) makes the first sync large — expect a long initial run per account.
- Deletion is conservative: `Expunge None` in the mbsync config means nothing is expunged server-side by sync.
- No OAuth2 and no Google People API contact sync; abook is the only address book.
