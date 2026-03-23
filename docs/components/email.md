# Email (NeoMutt Gmail Stack)

Terminal Gmail stack managed by chezmoi: `NeoMutt` + `mbsync` + `msmtp` + `notmuch` + `abook`.

Current rollout supports multiple enabled accounts rendered from `.chezmoidata.yaml`, with LaunchAgent automation active.

## Architecture

| Layer | Tool | Purpose | Managed Path |
|---|---|---|---|
| Sync | `mbsync` (`isync`) | IMAP sync into Maildir | `~/.config/isyncrc` |
| Send | `msmtp` | SMTP send via Gmail | `~/.config/msmtp/config` |
| Index/Search | `notmuch` | Unified inbox + fast search + tags | `~/.config/notmuch/default/config` |
| Client | `NeoMutt` | Mail UI, mailbox views, compose flow | `~/.config/neomutt/` |
| Contacts | `abook` | Local contact store + completion | `~/.config/abook/abookrc`, `~/.local/share/abook/addressbook` |
| Orchestration | `mail-sync` | Locking, logging, sync + index pipeline | `~/bin/mail-sync` |
| Scheduling | `launchd` LaunchAgent | Run `mail-sync --quiet` at login + interval | `~/Library/LaunchAgents/com.mbastakis.mail-sync.plist` |

## Why App Passwords In v1

- v1 uses one Gmail app password per account for both IMAP and SMTP.
- This keeps setup and long-term maintenance simpler than personal OAuth2 consent/token management.
- OAuth2 + Google Contacts sync is deferred to a later optional phase.

## First-Time Setup

Complete these steps before relying on daily automation:

1. Enable 2-Step Verification for each Gmail account.
2. Confirm app passwords are allowed (not blocked by Advanced Protection or org policy).
3. Create one app password per account.
4. Store each app password as a Bitwarden secret.
5. Record each UUID in `.chezmoidata.yaml` under `mail.accounts[].secrets.app_password_uuid`.
6. Recommended rollout: validate one pilot account first, then enable remaining accounts.
7. In Gmail web settings, keep IMAP enabled and required folders visible (`INBOX`, `[Gmail]/Sent Mail`, `[Gmail]/Drafts`, `[Gmail]/Spam`, `[Gmail]/Trash`).
8. Treat `sync_all_mail` as an explicit per-account opt-in; enabling it can trigger a very large first archive sync.

Apply + validate baseline:

```bash
chezmoi apply
mail-sync --dry-run --quiet
neomutt -n -F "$HOME/.config/neomutt/neomuttrc" -D
```

## Daily Workflow

| Command | Purpose |
|---|---|
| `nm` | Open NeoMutt |
| `msync` | Run sync/index pipeline now |
| `mail-sync --dry-run` | Preview IMAP sync without index mutation |
| `mail-sync --account mbastakis` | Sync a single account/channel |
| `ab` | Open `abook` contact editor |

Useful notmuch checks:

```bash
notmuch search 'tag:inbox and not tag:spam and not tag:trash'
notmuch search 'tag:acct-mbastakis and tag:inbox'
```

## NeoMutt Mailbox Workflow

- Unified inbox is a notmuch virtual mailbox over all enabled account inboxes: `tag:inbox and not tag:spam and not tag:trash`.
- Per-account inboxes are shown once in the sidebar as numbered physical Maildir rows (for example `[1] mbastakis Inbox`) so the visible label matches `i1`..`i9`.
- Per-account virtual mailboxes use account tags from `post-new` (for example `acct-mbastakis`) for sent/drafts/spam/trash views without duplicating inbox rows.
- NeoMutt hides noisy backend tags (for example account and role tags), keeps attachment/user labels visible, and appends transformed notmuch tags to the index when they matter.
- Folder/send hooks in `accounts.muttrc.tmpl` switch identity + `msmtp --account=<id>` and keep current-account mailbox targets in sync for role-jump macros.
- Local sent-copy duplication is disabled (`set record=""`) to avoid double-sent artifacts with Gmail.
- `virtual_spool_file=yes` makes the first virtual mailbox (`Unified Inbox`) the default startup/spool mailbox.

## Custom NeoMutt Keybindings

| Key | Action |
|---|---|
| `u` | Open unified inbox |
| `gg` | Jump to the top of the message list; in pager, jump to the top of the current mail |
| `G` | Jump to the bottom of the message list; in pager, jump to the bottom of the current mail |
| `gT` | Limit the current index view to the current thread (`l all` restores the full view) |
| `j` / `k` | In pager, scroll the current mail down/up by one line |
| `Up` / `Down` | In pager, jump to the previous/next mail |
| `i1`..`i9` | Jump to per-account inbox by account order (enabled accounts with `order` 1..9) |
| `gb` | Toggle sidebar visibility |
| `gf` | Search sidebar mailboxes |
| `gj` / `gk` | Move sidebar highlight down/up |
| `gl` | Edit notmuch labels on the current message |
| `gL` | Edit notmuch labels and immediately hide/requery if the result leaves the current view |
| `gn` / `gN` | Jump to next/previous sidebar mailbox with new mail |
| `go` | Open the highlighted sidebar mailbox |
| `gi` | Open current-account inbox |
| `gs` | Open current-account sent |
| `gd` | Open current-account drafts |
| `gp` | Open current-account spam |
| `gt` | Open current-account trash |
| `gU` | Use the message's `List-Unsubscribe` header when available |
| `gr` | Sync current account and reopen the current mailbox |
| `gq` | Prompt for a notmuch virtual folder query |
| `gu` | Open message URLs via compact `urlscan` list |

## NeoMutt Tuning

- Header view is intentionally weeded and ordered so the pager focuses on `From`, `To`, `Cc`, `Reply-To`, `Subject`, `Date`, and list metadata.
- `pager_read_delay=1` avoids marking a message read if you only preview it briefly.
- `pager_stop=yes` keeps `PageDown` inside the current mail instead of auto-advancing to the next message.
- `use_threads=threads` decouples thread display from sort order, so the index keeps a modern thread view while sorting by recent activity.
- `reply_with_xorig=yes` helps replies pick the delivered alias when `X-Original-To` is present.
- `abort_noattach=ask-yes` warns when you mention an attachment but forget to add one.
- Header cache compression is enabled with zlib level 1 to reduce cache size with minimal extra work.
- `read_inc=1000`, `write_inc=1000`, and `time_inc=500` reduce redraw overhead when opening/searching large folders.
- The sidebar uses a wider layout, hides empty folders, and shows cleaner `unread/total` counts.
- Colors use a stable Catppuccin-style 256-color palette so the mail UI renders reliably inside `tmux-256color`.
- Status/address flags use Nerd Font-friendly symbols instead of the default letter soup.
- In the attachment menu, pressing `Enter` on `image/*` now uses `mail-view-image`, which renders via `chafa`/Kitty graphics in Ghostty and falls back to `mail-open` if inline rendering fails.

## Automation Hook Point

After a successful non-dry-run sync, `mail-sync` executes executable files in:

- `mail.defaults.automation_hook_root` (default: `~/.config/mail/hooks/post-sync.d/`)

Behavior:

- non-executable files are skipped,
- hook failures are logged as warnings,
- sync completion still succeeds unless core sync/index steps fail.

## LaunchAgent Behavior

- Uses `RunAtLoad=true` and interval from `mail.defaults.sync_interval_minutes`.
- Calls `~/bin/mail-sync --quiet` directly (no dependence on interactive shell startup files).
- Launchd logs live under `mail.defaults.log_root` (default: `~/.local/state/mail/log/`).

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing tool/config/path errors | Run `chezmoi apply --dry-run --force` and `neomutt -n -F "$HOME/.config/neomutt/neomuttrc" -D` |
| IMAP auth failures | Recreate Gmail app password and verify Bitwarden UUID mapping |
| SMTP failures | Run `msmtp --serverinfo --account=<id>` |
| Unified inbox empty/stale | Run `mail-sync` and verify `notmuch config list` + `notmuch new` |
| `notmuch new` prints `.uidvalidity` notices | Safe Maildir metadata; `new.ignore=.uidvalidity` suppresses the noise |
| LaunchAgent not running | `plutil -lint ~/Library/LaunchAgents/com.mbastakis.mail-sync.plist` and `launchctl print gui/$(id -u)/com.mbastakis.mail-sync` |
| Contacts completion mismatch | Ensure `~/.config/abook/abookrc` and `~/.local/share/abook/addressbook` exist and `query_command` still points to both explicit paths |

Operational notes:

- First full sync can take a while for larger Gmail mailboxes.
- Initial `UIDVALIDITY` notices during first mailbox initialization are expected.
- Routine `.uidvalidity` files are ignored by `notmuch` and are not mail messages.

## Gmail Caveats (v1)

- `[Gmail]/All Mail` should remain an explicit per-account choice because the first sync can be large.
- Delete/expunge remains conservative (`Expunge None` in mbsync config).
- No OAuth2 and no Google People API contact sync in v1.

## Future OAuth2 Path (Optional)

Revisit OAuth2 only if app passwords become unavailable/unstable or Google Contacts sync becomes mandatory. Keep Maildir + NeoMutt + mbsync + msmtp + notmuch architecture unchanged and migrate auth separately.

## References

- `.chezmoidata.yaml`
- `private_dot_config/isyncrc.tmpl`
- `private_dot_config/msmtp/private_config.tmpl`
- `private_dot_config/notmuch/default/config.tmpl`
- `private_dot_config/notmuch/default/hooks/executable_post-new.tmpl`
- `private_dot_config/neomutt/neomuttrc.tmpl`
- `private_dot_config/neomutt/base.muttrc`
- `private_dot_config/neomutt/tags.muttrc.tmpl`
- `private_dot_config/neomutt/mailboxes.muttrc.tmpl`
- `private_dot_config/neomutt/bindings.muttrc.tmpl`
- `private_dot_config/neomutt/colors.muttrc.tmpl`
- `private_dot_config/neomutt/mailcap`
- `literal_bin/executable_mail-view-image`
- `literal_bin/executable_mail-sync.tmpl`
- `private_Library/LaunchAgents/com.mbastakis.mail-sync.plist.tmpl`
