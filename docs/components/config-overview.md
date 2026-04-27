# Config Overview

Summary of notable config areas managed by chezmoi, with links to dedicated docs for larger components.

**Source:** `private_dot_config/` -> `~/.config/`, `private_dot_local/private_share/` -> `~/.local/share/`

## Managed Components

| Component | Source Path | Dedicated Doc | Description |
|---|---|---|---|
| **Neovim** | `private_dot_config/nvim/` | [nvim.md](nvim.md) | Editor with lazy.nvim, LSP, custom keymaps |
| **OpenCode** | `private_dot_config/opencode/` | [opencode.md](opencode.md) | Primary AI CLI profile with agents, commands, and skills |
| **Karabiner** | `private_dot_config/private_karabiner/` | [karabiner.md](karabiner.md) | Keyboard remapping (generated config) |
| **Carapace** | `private_dot_config/carapace/` | [carapace.md](carapace.md) | Shell completion framework |
| **Zsh** | `private_dot_config/zsh/`, `dot_zshenv.tmpl` | [zsh.md](zsh.md) | Shell bootstrap plus XDG-aware tool/runtime environment |
| **Atuin** | `private_dot_config/private_atuin/private_config.toml` | -- | Shell history search, sync, and AI settings |
| Terraform CLI | `private_dot_config/terraform/terraform.rc` | -- | CLI defaults (for example checkpoint suppression) |
| **NeoMutt** | `private_dot_config/neomutt/` | [email.md](email.md) | Terminal mail client config and custom mailbox bindings |
| **notmuch** | `private_dot_config/notmuch/default/` | [email.md](email.md) | Mail index/search config and tagging hook |
| **msmtp** | `private_dot_config/msmtp/private_config.tmpl` | [email.md](email.md) | SMTP account config rendered from Bitwarden secrets |
| **isync (mbsync)** | `private_dot_config/isyncrc.tmpl` | [email.md](email.md) | IMAP sync channels and Maildir mapping |
| **abook** | `private_dot_config/abook/`, `private_dot_local/private_share/abook/` | [email.md](email.md) | Local address book split across XDG config/data paths |
| Colima | `private_dot_local/private_share/colima/` | -- | Container runtime config and VM state |
| Mise | `private_dot_config/mise/config.toml` (global) + `mise.toml` (repo root, source-only) | -- | Tool/version manager; repo-local pins `go-task` |
| Taskfile | `Taskfile.yml` (repo root, source-only) | -- | go-task runner for chezmoi repo workflows (apply/diff/lint/docs) |
| Ghostty | `private_dot_config/ghostty/` | -- | Terminal emulator |
| tmux | `private_dot_config/tmux/` | -- | Terminal multiplexer |
| Starship | `private_dot_config/starship.toml` | -- | Prompt theme |
| Git | `private_dot_config/git/` | -- | Git config and work profile |
| Bat | `private_dot_config/bat/` | -- | Cat replacement with syntax highlighting |
| Taskwarrior | `private_dot_config/task/` | -- | CLI todo list manager, XDG paths, Linear UDAs, Timewarrior hook (data at `~/.local/share/task/`) |
| Timewarrior | `private_dot_local/private_share/timewarrior/` | -- | CLI time tracker paired with Taskwarrior via `on-modify.timewarrior` hook |
| Yazi | `private_dot_config/yazi/` | -- | Terminal file manager |
| Lazygit | `private_dot_config/lazygit/` | -- | Git TUI |
| Brew | `private_dot_config/brew/` | -- | Homebrew Brewfile |
| Aerospace | `private_dot_config/aerospace/` | -- | macOS window manager (Darwin only) |
| Finicky | `private_dot_config/finicky/` | -- | macOS browser routing (Darwin only) |
| SketchyBar | `private_dot_config/sketchybar/` | -- | macOS status bar (Darwin only) |
| Raycast | `private_dot_config/raycast/` | -- | macOS launcher (partial, extensions ignored) |
| glab CLI | `private_dot_config/glab-cli/` | -- | GitLab CLI (DT work profile only) |
| Diffnav | `private_dot_config/diffnav/` | -- | Git diff TUI pager (file tree + delta rendering), invoked via `smart-diffnav` wrapper for TTY-aware behavior |
| gh-dash | `private_dot_config/gh-dash/` | -- | GitHub dashboard TUI (`gh` extension, Catppuccin Mocha Mauve) |

## Ghostty

Terminal emulator. Key configuration areas:

- **Theme:** Catppuccin Mocha, 80% background opacity with blur
- **Font:** JetBrainsMono Nerd Font Mono, size 21, ligatures enabled
- **Cursor:** Block with blink, hidden while typing
- **macOS:** Option-as-alt, hidden titlebar, global quick terminal (`Cmd+Ctrl+T`)
- **Keybindings:** Splits, tab management, Dvorak-layout pane navigation, CSI sequences for zsh integration

Custom keybindings are documented in [shortcuts.md](../shortcuts.md).

_Reference: `private_dot_config/ghostty/config:1`_

## tmux

Terminal multiplexer with Catppuccin theme and plugin ecosystem.

- **Prefix:** `Ctrl-a`
- **Plugins (TPM):** vim-tmux-navigator, catppuccin, tmux-smooth-scroll, tmux-yank, tmux-resurrect, tmux-continuum, tmux-floax, tmux-harpoon
- **Session picker:** `prefix + s` opens a `sesh` + `gum` popup helper (`~/bin/sesh-picker`)
- **Session rename:** `prefix + R` opens a `gum` input popup (`~/bin/sesh-rename`); rejects duplicate session names
- **OpenCode launch:** `prefix + o` splits the current pane and runs `~/bin/opencode-launch`, which checks `aws-login --auth-status claude-code` and uses the Claude profile only when the local cache is valid.
- **Session persistence:** Resurrect auto-saves every 15 min (via Continuum) and on every client detach. Restore on server start is handled by a custom `~/bin/tmux-restore` script that validates the save file and falls back to recent backups when the latest save is corrupt. OpenCode panes are restored to their exact previous session via per-pane session ID tracking in `~/.local/state/opencode/tmux-panes/`.
- **Status line:** Top position, oasis-style mode indicator with per-mode colors/icons
- **History:** 100,000 lines, mouse enabled, base-index 1

Custom keybindings are documented in [shortcuts.md](../shortcuts.md).

_Reference: `private_dot_config/tmux/tmux.conf:1`_

## sesh

Standalone tmux session manager used by the `prefix + s` popup helper.

- **Config:** `~/.config/sesh/sesh.toml`
- **Defaults:** single-part session names (`dir_length = 1`), cache + strict mode enabled, config sessions listed before tmux sessions and zoxide entries
- **Pinned sessions:** `main`, `dotfiles`, `notes`, and `ma-proj` (via work-only import)
- **Startup layout:** new sessions split into a zoomed shell pane running `eza -la --git --icons` plus a right-hand pane running `~/bin/opencode-launch`
- **Helper scripts:** `~/bin/sesh-picker` (fuzzy session picker), `~/bin/sesh-rename` (rename with duplicate-name guard), `~/bin/opencode-launch` (auth-aware OpenCode launcher with tmux session resume)

_Reference: `private_dot_config/sesh/sesh.toml:1`_

## Git

Git configuration with optional work profile:

- Base config at `~/.config/git/config`
- Work-specific config at `~/.config/git/.gitconfig-work` (DT work profile only, conditional include)
- Uses `smart-diffnav` as `git diff`/`git show` pager — a TTY-aware wrapper that invokes diffnav in interactive terminals and falls back to cat in agent/non-TTY contexts (e.g. OpenCode)
- Delta remains as `core.pager` for non-diff git output (log, blame) and as interactive diffFilter
- Catppuccin Mocha theme via delta's `[delta]` config section

_Reference: `private_dot_config/git/`_

## Brew

Homebrew Brewfile at `~/.config/brew/Brewfile`. Managed by the lifecycle script `02-install-packages` which runs `brew bundle` when the Brewfile content changes.

`aws-login` is installed from the private tap `mbastakis/tap` (formula `mbastakis/tap/aws-login`) instead of being compiled from dotfiles source.

_Reference: `private_dot_config/brew/Brewfile`_

## Taskwarrior

CLI todo list manager configured to be the primary project/task tracker (replacing Linear).

- **Config:** `~/.config/task/taskrc` (XDG override of default `~/.taskrc`, wired via `TASKRC`/`TASKDATA` env vars in `.zshenv`)
- **Theme:** `~/.config/task/mocha.theme` — Catppuccin Mocha colors (included from `taskrc`). Since Taskwarrior does not support hex colors, the palette is mapped to the nearest xterm-256 indexes.
- **Data:** `~/.local/share/task/taskchampion.sqlite3` (ignored by chezmoi)
- **Default report:** `task` with no args runs `task next` (via `default.command=next`)

### Linear UDAs

Seven user-defined attributes preserve Linear provenance for tasks originally imported from Linear:

| UDA | Purpose |
|---|---|
| `linear_id` | Linear issue identifier (e.g. `MBA-79`) |
| `linear_url` | Full Linear URL for quick browser jump |
| `linear_state` | Original Linear state name (Backlog / Todo / In Progress / In Review / Done / Canceled / Duplicate) |
| `linear_team` | Linear team key |
| `linear_assignee` | Linear assignee email |
| `linear_project` | Original Linear project name (pre-kebab-case) |
| `linear_estimate` | Linear point estimate (numeric) |

All Linear-origin tasks also carry the `+linear` tag for quick filtering:

```bash
task +linear list                     # all tasks imported from Linear
task linear_id:MBA-79 info            # look up by Linear ID
task linear_state:Todo +linear list   # only originally-Todo items
```

### Priority and label mapping

Linear priorities are mapped onto Taskwarrior's H/M/L scale: `Urgent` and `High` both become `H`, `Medium` becomes `M`, `Low` becomes `L`, and `None` leaves priority empty. `Urgent` issues additionally gain a `+urgent` tag so they stay distinguishable. Linear labels are lowercased and carried through as Taskwarrior tags.

### Timewarrior integration

The `on-modify.timewarrior` hook (vendored at `private_dot_config/task/hooks/executable_on-modify.timewarrior`, deployed to `~/.config/task/hooks/on-modify.timewarrior` with `+x`) bridges start/stop events to Timewarrior. `taskrc` sets `hooks.location=~/.config/task/hooks` so the hook is picked up automatically. See the [Timewarrior section](#timewarrior) below.

_Reference: `private_dot_config/task/taskrc`_

## Timewarrior

CLI time tracker paired with Taskwarrior. `task start N` auto-invokes `timew start` with the task's description, project, and tags; `task stop N` mirrors to `timew stop`.

- **Config:** `~/.local/share/timewarrior/timewarrior.cfg` (Timewarrior insists on keeping config and data in the same directory; path is set via `TIMEWARRIORDB` in `.zshenv`)
- **Theme:** `~/.local/share/timewarrior/mocha.theme` — Catppuccin Mocha colors imported from the main cfg, mirrors the Taskwarrior `mocha.theme` for visual consistency
- **Data:** `~/.local/share/timewarrior/data/` (ignored by chezmoi)
- **Bridge hook:** `~/.config/task/hooks/on-modify.timewarrior` (vendored from upstream `GothenburgBitFactory/timewarrior@stable`)

### Working hours

Exclusions are configured for Mon–Fri 09:00–18:00 with a 13:00–14:00 lunch window. Weekends are fully excluded. `timew day` / `timew week` / `timew month` charts default to `hours = working`, so non-work time stays out of the chart unless you explicitly request it.

### Common commands

```bash
timew                 # current tracking status
timew day             # today's intervals chart
timew week            # this week's chart
timew summary :week   # totals per tag this week
timew continue        # resume the last stopped interval
timew cancel          # abandon the active interval (no record)
```

### Taskwarrior bridge in practice

```bash
task add "Refactor auth middleware" project:api +backend
task start 42         # timew start "Refactor auth middleware" api backend
task stop 42          # timew stop
task 42 modify +urgent
                      # timew untag / retag with the new tag set
```

_Reference: `private_dot_local/private_share/timewarrior/timewarrior.cfg`_

## References

- Neovim AGENTS: `private_dot_config/nvim/AGENTS.md:1`
- OpenCode README: `private_dot_config/opencode/README.md:1`
- Email stack doc: `docs/components/email.md:1`
- mbsync template: `private_dot_config/isyncrc.tmpl:1`
- Ghostty config: `private_dot_config/ghostty/config:1`
- tmux config: `private_dot_config/tmux/tmux.conf:1`
- Key paths table: `AGENTS.md:78`
