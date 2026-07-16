# Config Overview

Summary of notable config areas managed by chezmoi, with links to dedicated docs for larger components.

**Source:** `private_dot_config/` -> `~/.config/`, `private_dot_local/private_share/` -> `~/.local/share/`

## Managed Components

| Component | Source Path | Dedicated Doc | Description |
|---|---|---|---|
| **Neovim** | `private_dot_config/nvim/` | [nvim.md](nvim.md) | Editor with lazy.nvim, LSP, custom keymaps |
| **OpenCode** | `private_dot_config/opencode/`, `private_dot_config/oauth2-proxy/` | [opencode.md](opencode.md) | Shared AI session server with local attached TUIs and Authentik-protected, tailnet-only mobile PWA access |
| **Pi** | `private_dot_config/pi/` | -- | Pi global config rooted at `~/.config/pi`, including settings, keybindings, extensions, prompt templates, and Pi-specific skills |
| **Shared Agent Skills** | `private_dot_agents/skills/` | [opencode.md](opencode.md#skills) | Harness-agnostic skills loaded from `~/.agents/skills/` by OpenCode and Pi |
| **Karabiner** | `private_dot_config/private_karabiner/` | [karabiner.md](karabiner.md) | Keyboard remapping (generated config) |
| **Carapace** | `private_dot_config/carapace/` | [carapace.md](carapace.md) | Shell completion framework |
| **Zsh** | `private_dot_config/zsh/`, `dot_zshenv.tmpl` | [zsh.md](zsh.md) | Shell bootstrap plus XDG-aware tool/runtime environment |
| **SSH** | `private_dot_ssh/`, `literal_bin/executable_homeserver-route` | -- | Encrypted/private SSH keys plus host aliases; Atlas and TrueNAS aliases verify the pinned LAN host key, prefer the local route, and fall back to Tailscale |
| **Atuin** | `private_dot_config/private_atuin/private_config.toml` | -- | Shell history search, sync, and AI settings |
| Terraform CLI | `private_dot_config/terraform/terraform.rc` | -- | Legacy Terraform CLI defaults (for example checkpoint suppression); homeserver IaC uses repo-local OpenTofu instead |
| **NeoMutt** | `private_dot_config/neomutt/` | [email.md](email.md) | Terminal mail client config and custom mailbox bindings |
| **notmuch** | `private_dot_config/notmuch/default/` | [email.md](email.md) | Mail index/search config and tagging hook |
| **msmtp** | `private_dot_config/msmtp/private_config.tmpl` | [email.md](email.md) | SMTP account config rendered from Bitwarden secrets |
| **isync (mbsync)** | `private_dot_config/isyncrc.tmpl` | [email.md](email.md) | IMAP sync channels and Maildir mapping |
| **abook** | `private_dot_config/abook/`, `private_dot_local/private_share/abook/` | [email.md](email.md) | Local address book split across XDG config/data paths |
| Colima | `private_dot_local/private_share/colima/` | -- | Container runtime seed; live VM config is preserved after creation |
| Kubernetes | `private_dot_config/kube/` | -- | DT work kubeconfig seeds; live files are preserved after `kubectl`/`aws`/`kind` rewrites |
| aws-login | `private_dot_config/aws-login/` | -- | Work and personal AWS profiles, AWS SSO bootstrap, and per-profile `KUBECONFIG` wiring |
| Mise | `private_dot_config/mise/config.toml` (global) + `mise.toml` (repo root, source-only) | -- | Tool/version manager; repo-local pins Node, Python, uv, go-task, OpenTofu, TFLint, terraform-docs, pre-commit, jq, yq, ShellCheck, and yamllint |
| Homeserver Python | `infra/pyproject.toml`, `infra/src/homeserver_iac/`, `infra/schemas/`, `infra/tests/` (source-only) | [homeserver-iac.md](../architecture/homeserver-iac.md#typed-desired-state) | Pydantic contracts plus typed BWS, TrueNAS, Backrest, and Syncthing reconcilers with secret-safe plans and fixture tests; invoked publicly through Task only |
| Taskfile | `Taskfile.yml` + `infra/**/Taskfile.yml` (source-only) | -- | Thin root go-task interface with AWS, TrueNAS, identity, network, sync, Atlas, Sisyphus browser tests, typed desired-state, and aggregate validation tasks |
| Ghostty | `private_dot_config/ghostty/` | -- | Terminal emulator |
| tmux | `private_dot_config/tmux/` | -- | Terminal multiplexer |
| Starship | `private_dot_config/starship.toml` | -- | Prompt theme |
| Git | `private_dot_config/git/` | -- | Git config and work profile |
| Bat | `private_dot_config/bat/` | -- | Cat replacement with syntax highlighting |
| Taskwarrior | `private_dot_config/task/` | -- | CLI todo list manager, XDG paths, Linear UDAs (data at `~/.local/share/task/`) |
| Yazi | `private_dot_config/yazi/` | -- | Terminal file manager |
| Lazygit | `private_dot_config/lazygit/` | -- | Git TUI |
| Brew | `private_dot_config/brew/`, `private_dot_config/homebrew/` | -- | Homebrew Brewfile, including OpenCode/oauth2-proxy runtime dependencies, and package trust allowlist |
| Aerospace | `private_dot_config/aerospace/` | -- | macOS window manager (Darwin only) |
| Finicky | `private_dot_config/finicky/` | -- | macOS browser routing (Darwin only) |
| Raycast | `private_dot_config/raycast/` | -- | macOS launcher (partial, extensions ignored) |
| glab CLI | `private_dot_config/glab-cli/` | -- | GitLab CLI config seed; live auth-bearing config is preserved (DT work profile only) |
| Diffnav | `private_dot_config/diffnav/` | -- | Git diff TUI pager (file tree + delta rendering), invoked via `smart-diffnav` wrapper for TTY-aware behavior |
| gh-dash | `private_dot_config/gh-dash/` | -- | GitHub dashboard TUI (`gh` extension, Catppuccin Mocha Mauve) |

Repo-local pre-commit hygiene hooks skip `private_Documents/notes/dot_obsidian/` for whitespace and final-newline rewrites because Obsidian and its plugins own that JSON/manifest formatting at runtime.

## Repository Workflows

The root `Taskfile.yml` owns repository-level commands and includes Taskfiles
next to the infrastructure they operate. Domain commands use `aws:*`,
`truenas:*`, `identity:*`, `network:*`, `sync:*`, and `atlas:*`. Old deployment
aliases were removed; `tf:*` now contains only cross-stack OpenTofu quality and
state commands.

Run the complete secret-free, live-service-free infrastructure gate from the
repository root:

```bash
mise exec -- task infra:validate
```

After cloning or changing `infra/pyproject.toml`, install the committed Python
lock once with `mise exec -- task infra:python:sync`. Normal validation uses uv
in locked offline mode. Use `infra:desired:validate` for all versioned YAML
contracts, `infra:python:validate` for the Python quality gate, and
`infra:schemas:generate` only when a Pydantic contract intentionally changes.
Live typed plans use `truenas:apps:plan`, `truenas:snapshots:plan`,
`truenas:nfs:plan`, `truenas:smb:plan`, `truenas:backrest:plan`,
`truenas:api-key:plan`, and `sync:plan:all`. Run
`infra:status` to aggregate every live read-only domain check. Superseded shell
reconcilers and rollback aliases have been removed.

The migration-only `infra:photos:validate-export` task scans an Apple Photos
export without changing it, checks content type, fully decodes each visual
stream with FFmpeg, and writes a JSON report outside the export tree.
`infra:photos:build-import-manifest` then joins validated media to explicit
source snapshots and binds selected media and XMP sidecars to SHA-256 hashes.
`infra:photos:plan-immich-metadata` reconciles the import manifest with official
Immich CLI upload evidence and emits the read-only favorite, album, and stack
API plan before any temporary API key is created. The separate
`infra:photos:reconcile-immich-metadata` task performs the bounded live API
comparison from that reviewed plan and only mutates when `APPLY=true` is passed;
its stack verifier treats Immich `livePhotoVideoId` links as present Live Photo
motion assets while still blocking unrelated stack differences.
These are live-data operations and are intentionally excluded from
`infra:validate`.

The Tailscale whole-policy document is managed by the official provider in its
own state through `network:policy:plan` and `network:policy:apply`. Those tasks
inject the API credential from BWS and run the separate remote validator first;
the pinned provider release does not yet perform remote validation during plan.

Use `atlas:validate` for local playbook syntax checks, `atlas:*:plan` for
Ansible check mode with diff output, and `atlas:*:apply` for convergence. Check
mode is advisory because not every Ansible module can fully model a remote
mutation without applying it. `atlas:taskboard:test` runs an isolated
real-Taskwarrior HTTP mutation lifecycle and mocked Playwright UI regressions,
while `atlas:taskboard:smoke:live` opens a read-only SSH tunnel to
the deployed container. The live smoke runs automatically after
`atlas:homeserver:apply`.

Atlas homeserver convergence uses native Ansible file management and the
`community.docker.docker_compose_v2` module. A focused local module updates the
TrueNAS middleware user record for the backup SSH key because direct
`authorized_keys` edits would bypass the appliance-owned user database.

Before moving OpenTofu resources or stack source paths, run
`mise exec -- task tf:state:baseline` and follow the
[state migration runbook](../runbooks/opentofu-state-migrations.md). The live
check verifies versioned state recovery points and provider lock metadata; it
is intentionally excluded from the offline `infra:validate` gate.

Run `mise exec -- task tf:test` after changing a reusable OpenTofu module. The
task initializes each module test root against its committed provider lockfile
and runs mock-provider tests without reading live infrastructure. Provider
installation may require network access on a fresh workstation, so module tests
remain separate from the strictly offline aggregate gate.

## Pi

Global Pi config lives under `~/.config/pi` via `PI_CODING_AGENT_DIR`. `settings.json` installs `npm:pi-web-access` for web search, URL fetching, GitHub repo cloning, PDF extraction, and video/YouTube analysis tools, `npm:pi-annotate` for visual annotation with inline note cards, and `npm:pi-subagents` for optional delegated research/execution workflows. It also keeps `npm:@injaneity/pi-computer-use` installed but filters its `extensions` to `[]`, so macOS computer-use tools such as `list_apps`, `list_windows`, `screenshot`, and GUI actions are not loaded by default. The local `computer-use-toggle` extension adds `/computer-use-enable` to opt in for the current Pi session, `/computer-use-disable` to unload it again, and `/computer-use-status` to inspect state; future sessions remain disabled unless enabled again. Prompt templates live directly under `private_dot_config/pi/prompts/`; `research_codebase.md` expands as `/research_codebase` and documents codebases as-is, using Pi subagents when available and `thoughts/` as historical context when present. Package code is installed under ignored `~/.config/pi/npm/`; the computer-use native helper is placed at `~/.pi/agent/helpers/pi-computer-use/bridge` and needs macOS Accessibility and Screen Recording permissions on first use.

The local `powerline-footer` extension is vendored from `nicobailon/pi-powerline-footer` under `private_dot_config/pi/extensions/powerline-footer/` and patched to respect `PI_CODING_AGENT_DIR` via Pi's `getAgentDir()`. Powerline settings are code-managed in `settings.json`: Catppuccin Mocha segment colors come from the extension-local `theme.json`, high thinking levels use fixed Catppuccin warning/error colors instead of the upstream rainbow gradient, the thinking label is shortened (`think:xh`), the context segment is right-aligned and shows exact token counts, subscription cost noise is hidden, cache/cost details overflow to the secondary row, fixed-editor mode is off by default for a less invasive startup, and `/powerline fixed-editor on` opts into the fixed editor cluster. Runtime stash/bash history and generated vibe files live under ignored `~/.config/pi/powerline-footer/` and `~/.config/pi/vibes/`.

The local `context-inspector` extension provides `/context`; default HTML/JSON exports now go to the OS temp directory under `pi-context-snapshots/` with private file permissions instead of project-local `.pi/` paths, because snapshots can contain prompts, tool calls, file contents, and secrets.

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

Terminal multiplexer with Catppuccin theme and plugin ecosystem on the workstation, and the same shared config in a server-safe mode on SSH hosts such as `atlas`.

- **Prefix:** `Ctrl-a` everywhere. In nested SSH tmux sessions, use `Ctrl-a a` to forward one prefix to the remote tmux, then press the remote command key.
- **Plugins (TPM):** vim-tmux-navigator, catppuccin, tmux-yank, tmux-resurrect, tmux-continuum, tmux-floax, tmux-harpoon
- **Server mode:** SSH sessions skip TPM startup, Mac-only helper scripts, and the workstation status line while keeping the core pane/window/copy-mode behavior.
- **Clipboard:** tmux allows OSC52 clipboard forwarding so yanks from remote Neovim can reach the workstation terminal clipboard. The atlas Ansible role reloads a running tmux server when the shared tmux config changes so existing sessions pick up `set-clipboard on` and passthrough settings.
- **Session picker:** `prefix + s` opens a `sesh` + `gum` popup helper (`~/bin/sesh-picker`)
- **Session rename:** `prefix + R` opens a `gum` input popup (`~/bin/sesh-rename`); rejects duplicate session names
- **OpenCode launch:** `prefix + o` splits the current pane and runs `~/bin/opencode-launch`, which preserves per-pane OpenCode session tracking across tmux restores.
- **OpenCode sidebar:** `prefix + O` toggles a 28-column Catppuccin-styled left sidebar. It opens immediately from a short-lived cache, refreshes asynchronously, and lists live OpenCode panes with color-coded status dots. Rows are mouse-clickable and jump to the exact tmux session, window, and pane. Opening focuses the sidebar; closing preserves the active app pane or returns to the pre-sidebar pane when necessary. Sidebars are created lazily as tmux windows are visited, hiding them reapplies each window's exact pre-sidebar layout, and closing a window's last application pane also closes its sidebar.
- **Scrollback:** `PageUp`/`PageDown` move by half-pages in tmux copy-mode scrollback, but are forwarded to fullscreen pane applications using the alternate screen.
- **URL opening:** double-clicking a URL in a pane opens it with the system browser via `~/bin/tmux-open-url-at-mouse`; non-URL double-clicks keep tmux's default word-copy behavior.
- **Pane separators:** tmux uses shared separator cells rather than independent pane boxes; the config uses thin active blue/inactive gray separator styling and top pane labels to approximate boxed panes.
- **Session persistence:** Resurrect auto-saves every 15 min (via Continuum) and on every client detach. `~/bin/tmux-save` serializes save requests, removes managed sidebar panes before saving, synchronizes live OpenCode IDs, pins those IDs in the saved launch commands, and then recreates the sidebars. Restore on server start is handled by `~/bin/tmux-restore`, which validates the save file, falls back to recent backups when needed, and reapplies the persisted sidebar preference. OpenCode panes are therefore restored independently of pane renumbering; `occ` also rejects saved IDs from another project directory. Separate live mappings under `~/.local/state/opencode/tmux-session-state/panes/` are synchronized by the attached TUI plugin and removed when panes exit or become stale.
- **Status line:** Top position, oasis-style mode indicator with per-mode colors/icons
- **History:** 100,000 lines, mouse enabled, base-index 1

Custom keybindings are documented in [shortcuts.md](../shortcuts.md).

_Reference: `private_dot_config/tmux/tmux.conf:1`_

## Yazi

Terminal file manager. `atlas` receives the shared config from `private_dot_config/yazi/` via Ansible, installs the upstream `yazi` `.deb` matching the workstation version, and runs `ya pkg install` against `package.toml` for plugins.

_Reference: `private_dot_config/yazi/yazi.toml:1`, `infra/atlas/ansible/roles/terminal_comfort/tasks/main.yml:84`_

## Lazygit

Git TUI with Catppuccin-style colors and `delta --dark --paging=never` as the pager. `atlas` receives the same `private_dot_config/lazygit/config.yml` via Ansible and installs Ubuntu's `git-delta` package so the pager command resolves to `delta`.

_Reference: `private_dot_config/lazygit/config.yml:1`, `infra/atlas/ansible/roles/terminal_comfort/tasks/main.yml:76`_

## sesh

Standalone tmux session manager used by the `prefix + s` popup helper.

- **Config:** `~/.config/sesh/sesh.toml`
- **Defaults:** single-part session names (`dir_length = 1`), cache + strict mode enabled, config sessions listed before tmux sessions and zoxide entries
- **Pinned sessions:** `main`, `dotfiles`, `notes`, and `ma-proj` (via work-only import)
- **Startup layout:** new sessions start as a plain single-window tmux session by default
- **Helper scripts:** `~/bin/sesh-picker` (fuzzy session picker), `~/bin/sesh-rename` (rename with duplicate-name guard), `~/bin/opencode-launch` (OpenCode launcher with tmux session resume), `~/bin/opencode-session-picker` (live OpenCode pane data), `~/bin/opencode-session-sidebar` (mouse-aware sidebar UI), `~/bin/tmux-opencode-sidebar` (sidebar lifecycle and layout)

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

Homebrew package trust is managed at `~/.config/homebrew/trust.json` using narrow formula- and cask-level allowlists for trusted third-party packages. The package lifecycle script stages this file before `brew bundle` because chezmoi before scripts run ahead of normal managed-file deployment.

`aws-login` is installed from the private tap `mbastakis/tap` (formula `mbastakis/tap/aws-login`) instead of being compiled from dotfiles source.

_Reference: `private_dot_config/brew/Brewfile`, `private_dot_config/homebrew/private_trust.json`_

## Taskwarrior

CLI todo list manager and single source of truth for personal task management, syncing Mac and iPhone through a TaskChampion sync server on atlas.

- **Config:** `~/.config/task/taskrc` (chezmoi template rendering sync encryption secret from BWS; XDG override of default `~/.taskrc`, wired via `TASKRC`/`TASKDATA` env vars in `.zshenv`)
- **Theme:** `~/.config/task/mocha.theme` — Catppuccin Mocha colors (included from `taskrc`). Since Taskwarrior does not support hex colors, the palette is mapped to the nearest xterm-256 indexes.
- **Data:** `~/.local/share/task/taskchampion.sqlite3` (ignored by chezmoi)
- **Default report:** `task` with no args runs `task next` (via `default.command=next`)
- **TUI:** `taskwarrior-tui` (Rust, vim-like navigation, keyboard-first, daily driver for terminal triage)
- **Sync:** TaskChampion sync server on atlas at `https://tasks.mbastakis.com` (Private Route53 + Traefik + Tailscale, no OIDC). The shared task-history client ID is hardcoded in `taskrc.tmpl` and allowlisted on atlas; the sync encryption secret is rendered from BWS.
- **Board:** Sisyphus runs on atlas at `https://taskboard.mbastakis.com` as a write-capable Kanban projection over Taskwarrior. It uses its own local Taskwarrior replica, syncs through TaskChampion, maps columns to native Taskwarrior state (`+next`, active/start, `+waiting`, done) rather than storing separate board state, and is gated by Authentik forward-auth at Traefik. Deployment identifiers remain `taskboard`.
- **Automation:** `~/bin/task-sync` runs `task sync` with a lock and logs to `~/.local/state/task/log/task-sync.log`; `~/Library/LaunchAgents/com.mbastakis.task-sync.plist` runs it at login and every 2 minutes.
- **iOS:** Taskchamp (native TaskChampion replica, list/sort/capture/start/stop/done). Use the same shared client ID as Mac: `24e1b420-97ae-4847-9fae-cf15c096706b`.
- **Timewarrior:** removed — recurring tasks are native Taskwarrior, time tracking had no sync story

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

_Reference: `private_dot_config/task/taskrc.tmpl`, `infra/atlas/ansible/roles/atlas_homeserver/files/taskboard/`, [sync architecture spec](../../specs/taskwarrior-sync-implementation-plan.md)_

## References

- Neovim AGENTS: `private_dot_config/nvim/AGENTS.md:1`
- OpenCode README: `private_dot_config/opencode/README.md:1`
- Homeserver IaC: `docs/architecture/homeserver-iac.md:1`
- Email stack doc: `docs/components/email.md:1`
- Taskwarrior sync architecture: `specs/taskwarrior-sync-implementation-plan.md:1`
- mbsync template: `private_dot_config/isyncrc.tmpl:1`
- Ghostty config: `private_dot_config/ghostty/config:1`
- tmux config: `private_dot_config/tmux/tmux.conf:1`
- Key paths table: `AGENTS.md:78`
