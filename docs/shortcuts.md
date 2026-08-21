# Shortcuts

Unified index of custom keymaps across all input layers. **Custom mappings only** — plugin-default keymaps are excluded (see [Excluded Mappings](#excluded-mappings)).

## Input Flow

```mermaid
flowchart LR
  K["Karabiner<br/>(keyboard layer)"] --> G["Ghostty<br/>(terminal layer)"]
  G --> T["tmux<br/>(multiplexer layer)"]
  G --> Z["zsh<br/>(shell layer)"]
  T --> Z
  Z --> M["NeoMutt<br/>(mail layer)"]
  Z --> N["Neovim<br/>(editor layer)"]
```

A keystroke passes through each layer in sequence. Karabiner processes physical key events first (home row mods, hyper key), Ghostty handles terminal-level bindings, tmux intercepts its prefix and pass-through sequences, zsh processes shell keybindings, and then app-level bindings apply in NeoMutt or Neovim.

## Vicinae

Source: `private_dot_config/vicinae/settings.json`. Spotlight's matching shortcuts are disabled by `literal_bin/executable_macos-settings.tmpl` so Vicinae owns the launcher chord.

| Key | Action |
| --- | --- |
| `Cmd+Space` | Toggle Vicinae |
| `Cmd+Shift+V` | Open Clipboard History |
| `Cmd+Shift+S` | Capture a selected region, equivalent to `Cmd+Shift+4` |
| `Cmd+Option+Space` | Cycle Qwerty, Dvorak, and Greek Dvorak input sources |

## AeroSpace

Source: `private_dot_config/aerospace/aerospace.toml`. Workspace bindings intentionally expose only workspaces `1`, `a`, `o`, `e`, `u`, and `j`.

| Key | Action |
| --- | --- |
| `Alt+1/A/O/E/U/J` | Switch to the corresponding workspace |
| `Alt+Shift+1/A/O/E/U/J` | Move the focused window to the corresponding workspace and follow it |

Vicinae is matched by bundle ID and forced to floating layout.

## Karabiner

### Build Pipeline

`karabiner.json` is **fully generated** — never edit it directly. `build.sh` assembles it from modular sources and validates the output with `jq` before writing:

```mermaid
flowchart TD
  A[src/base.json<br/>profile + devices] --> E[build.sh]
  B["src/rules/00-02<br/>anti-misfire rules"] --> E
  C["src/templates/hrm.json<br/>HRM template"] --> E
  D["src/rules/11-15<br/>feature rules"] --> E
  E -->|"HRM_CONFIG array<br/>generates rules 03-10"| F[karabiner.json]
```

To rebuild after editing any source file:

```bash
"$(chezmoi source-path)"/private_dot_config/private_karabiner/build.sh
```

### Home Row Mods (GASC)

Dual-function keys: tap for the letter, hold for a modifier. Timing lives in the `HRM_CONFIG` array in `private_dot_config/private_karabiner/executable_build.sh`.

| Key | Tap | Hold    | Finger | Streak window |
| --- | --- | ------- | ------ | ------------- |
| `a` | a   | Ctrl    | left pinky   | 160ms |
| `s` | s   | Option  | left ring    | 160ms |
| `d` | d   | Command | left middle  | 160ms |
| `f` | f   | Shift   | left index   | 50ms  |
| `j` | j   | Shift   | right index  | 50ms  |
| `k` | k   | Command | right middle | 160ms |
| `l` | l   | Option  | right ring   | 160ms |
| `;` | ;   | Ctrl    | right pinky  | 160ms |

The streak window is how recently you must have typed for the key to output a letter instead of arming a modifier. Index fingers get a much shorter window (50ms, with shorter hold/alone thresholds too) because they are the fastest typists — a longer window would swallow deliberate Shift holds.

### Anti-Misfire Protection

Five layers prevent accidental modifier activation during normal typing:

```mermaid
flowchart LR
  A[Keystroke] --> B[Layer 1<br/>Common Words]
  B --> C[Layer 2<br/>Bilateral Cancel]
  C --> D[Layer 3<br/>Crossover Timing]
  D --> E[Layer 4<br/>Streak Detection]
  E --> F[Layer 5<br/>Typing Mode]
  F --> G{Modifier<br/>or Letter?}
```

| Layer | Rule file (under `private_dot_config/private_karabiner/src/rules/`) | Purpose |
| --- | --- | --- |
| 1. Common Words | `00-common-words.json` | Fast cross-hand word patterns produce letters, not mods |
| 2. Bilateral Cancellation | `01-bilateral-cancellation.json` | Same-hand combos always produce letters |
| 3. Crossover Timing | `02-crossover-timing.json` | Cross-hand timing enforcement |
| 4. Streak Detection | _(generated rules 03-10)_ | Recent typing disables mod behavior, per-finger timeouts |
| 5. Typing Mode Toggle | `11-typing-mode-toggle.json` | `Right Cmd + Space` manually toggles all HRM off/on (with on-screen notification) |

### Hyper Key

| Key | Action | Source |
| --- | --- | --- |
| `Caps Lock` (hold) | Hyper mode (sets `hyper_caps_lock` while held) | `private_dot_config/private_karabiner/src/rules/13-hyper-key.json` |
| `Caps Lock` (tap) | Escape | `private_dot_config/private_karabiner/src/rules/13-hyper-key.json` |
| `Right Shift` (double-tap) | Caps Lock toggle | `private_dot_config/private_karabiner/src/rules/14-double-tap-caps.json` |

### Hyper Navigation (hold Caps Lock)

Source: `private_dot_config/private_karabiner/src/rules/15-hyper-navigation.json`

| Hyper + | Action |
| --- | --- |
| `j` / `;` | Left / Right arrow |
| `k` / `l` | Down / Up arrow |
| `h` | Escape |
| `d` / `f` | Cmd+Left / Cmd+Right (line start / end) |
| `y` / `o` | Home / End |
| `u` / `.` | Page Up |
| `n` / `,` | Page Down |
| `m` | Backspace |
| `a` | Left Option (combine with arrows for word movement) |

## Ghostty

Source: `private_dot_config/ghostty/config`. Most `Cmd` bindings inject tmux prefix sequences (`Ctrl+a` + key), so window management feels native while tmux does the work.

| Key | Action |
| --- | --- |
| `Cmd+T` | New tmux window (`prefix c`) |
| `Cmd+W` | Kill tmux pane (`prefix x`) |
| `Cmd+D` | Split horizontal (`prefix h`) |
| `Cmd+Shift+D` | Split vertical (`prefix v`) |
| `Cmd+P` | FloaX floating window (`prefix P`) |
| `Cmd+S` | Sesh session picker (`prefix s`) |
| `Cmd+H` | Previous tmux window (`prefix p`) |
| `Cmd+L` | Next tmux window (`prefix n`) |
| `Cmd+R` | Rename tmux window (`prefix ,`) |
| `Cmd+Shift+R` | Rename tmux session (`prefix R`) |
| `Cmd+Z` | Toggle tmux pane zoom (`prefix z`) |
| `Cmd+G` | Lazygit popup (`prefix G`) |
| `Cmd+Shift+T` | New Ghostty OS window |
| `Cmd+Shift+W` | Close Ghostty OS window |
| `Cmd+Backspace` | Delete to start of line (sends Ctrl+U) |
| `Ctrl+Shift+T` | Send `ESC[202~` to zsh (directory picker) |
| `Cmd+B` | Send `ESC[203~` to zsh (Worktrunk worktree picker) |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Pass through to tmux (next/previous window) |
| `Cmd+Left` / `Cmd+Right` | Home / End |
| `Cmd+Shift+E` | Write screen to file and open it |
| `Shift+Enter` | CSI `13;2u` (literal newline for TUIs) |
| `Super+0` | Reset font size |
| `Super+Shift+]` / `Super+-` | Increase / decrease font size |

Ghostty's macOS `Hide Ghostty` menu shortcut is remapped to `Ctrl+Option+Cmd+H` via `~/bin/macos-settings`, so `Cmd+H` reaches tmux window navigation while other apps keep the default hide shortcut.

## tmux

Source: `private_dot_config/tmux/tmux.conf`. Prefix: **`Ctrl-a`** everywhere. In a local pane attached to remote tmux over SSH, `Ctrl-a a` forwards one prefix to the remote tmux: `Ctrl-a h` splits locally, `Ctrl-a a h` splits the remote.

| Key | Action |
| --- | --- |
| `prefix h` / `prefix v` | Split horizontal / vertical (keeps current path) |
| `prefix H` / `prefix V` / `prefix T` | Arrange panes side-by-side / stacked / tiled grid |
| `prefix c` | New window (keeps current path) |
| `prefix x` | Kill pane (no confirm) |
| `prefix p` | Previous window |
| `prefix G` | Lazygit popup (90% overlay) |
| `prefix s` | Sesh session picker popup |
| `prefix ,` / `prefix R` | Rename window / session (popup prompts) |
| `prefix P` | FloaX floating window (`Alt+Shift+P` opens the FloaX menu) |
| `prefix r` | Reload tmux.conf |
| `prefix d` | Detach client |
| `prefix Arrow` | Resize pane (repeatable, 5 cells) |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Next / previous window (no prefix) |
| `Ctrl+Shift+Arrow` | Resize pane (no prefix) |
| `PageUp` / `PageDown` | Half-page scrollback in shell panes; forwarded to fullscreen apps |
| Double-click URL | Open URL in browser (non-URLs keep default word copy) |
| `v` / `Ctrl+V` (copy mode) | Begin selection / rectangle toggle |
| `y` (copy mode) | Copy selection and cancel |
| `Escape` (copy mode) | Cancel |

### Harpoon (tmux-harpoon)

| Key | Action |
| --- | --- |
| `Ctrl+Cmd+A/O/E/U` | Jump to slot 1-4 |
| `Ctrl+Cmd+Shift+A/O/E/U` | Overwrite slot 1-4 with current pane |
| `prefix A` | Add pane to harpoon |
| `prefix D` | Delete from harpoon |
| `prefix g` | List harpoon slots |
| `prefix e` | Edit harpoon list |

## Zsh

Workstation configuration; server-side terminal configuration is owned by Kavouki.

### Custom Widgets

Sources: `private_dot_config/zsh/keybindings.zsh`, `private_dot_config/zsh/fzf.zsh`, `private_dot_config/zsh/functions.zsh`.

| Key | Action |
| --- | --- |
| `Ctrl+F` | Interactive ripgrep search (`ftext`); `Enter` opens in editor, `Tab` inserts the filename |
| `Ctrl+J` | Insert literal newline (multiline editing) |
| `Ctrl+T` | FZF file picker (fd-based, bat preview) |
| `Ctrl+Shift+T` | FZF directory picker (via Ghostty `ESC[202~` passthrough) |
| `Ctrl+Z` | Zoxide interactive directory jump (`cdi`) |
| `Cmd+B` | Worktrunk worktree picker (`wt switch`, via Ghostty `ESC[203~` passthrough) |
| `Ctrl+R` | Atuin history search (fzf's binding is removed) |
| `?` | Atuin AI widget; `Tab` inserts the generated command |

### Word and Line Movement

Source: `private_dot_config/zsh/keybindings.zsh`. Multiple escape sequences are bound so Alt, Ctrl, and Cmd arrow variants all work.

| Key | Action |
| --- | --- |
| `Alt+F` / `Ctrl+Right` | Forward word (also accepts one autosuggestion word) |
| `Alt+B` / `Ctrl+Left` | Backward word |
| `Home` / `Cmd+Left` | Beginning of line |
| `End` / `Cmd+Right` | End of line |

### Shift-Select

Source: `private_dot_config/zsh/shift-select-enhancements.zsh` (extends the zsh-shift-select plugin).

| Key | Action |
| --- | --- |
| `Shift+Cmd+Left/Right` | Select entire line |
| `ESC[200~` / `ESC[201~` | Copy / cut active selection to clipboard (custom CSI sequences; the Ghostty config does not currently emit them) |

### FZF Internal Bindings (inside any fzf)

Source: `private_dot_config/zsh/fzf.zsh` (`FZF_DEFAULT_OPTS`).

| Key | Action |
| --- | --- |
| `Ctrl+/` | Toggle preview |
| `Ctrl+D` / `Ctrl+U` | Preview page down / up |
| `Ctrl+Y` | Copy entry to clipboard |
| `Ctrl+A` | Toggle all selections |
| `Ctrl+S` | Toggle sort |

### FZF-Tab (inside completion menu)

Source: `private_dot_config/zsh/fzf-tab.zsh`.

| Key | Action |
| --- | --- |
| `<` / `>` | Switch completion group |
| `/` | Accept and continue into subdirectory |

### Command Aliases

Source: `private_dot_config/zsh/aliases.zsh` (selection; see the file for listing/eza variants).

| Alias | Expands to |
| --- | --- |
| `v` | `NVIM_APPNAME=nvim-native nvim` |
| `vi`, `vim` | `nvim` |
| `lg` | `lazygit` |
| `nm` / `msync` | `neomutt` / `mail-sync` |
| `oc` / `occ` / `ocserve` | `opencode-launch` / `opencode-launch --continue` / `opencode-server` |
| `cz` | `chezmoi` |
| `ta` / `td` / `tls` | `tmux attach` / `tmux detach` / `tmux ls` |
| `k` / `ctx` / `ns` | `kubectl` / `kubectx` / `kubens` |
| `grt` | `cd` to git repo root |
| `r`, `reload` | Replace shell with fresh instance |
| `lssh` | `lazyssh` |

## NeoMutt

Source: `private_dot_config/neomutt/bindings.muttrc.tmpl` (the only bindings file; rendered per enabled mail account). `i` and `g` are unbound (`noop`) so they act purely as prefixes.

| Key | Action |
| --- | --- |
| `u` | Open unified inbox virtual mailbox |
| `gg` | Top of index; in pager, top of current mail |
| `G` | Bottom of index; in pager, bottom of current mail |
| `gT` | Limit index to current thread (`l all` restores full view) |
| `j` / `k` (pager) | Scroll current mail down / up one line |
| `Up` / `Down` (pager) | Previous / next undeleted mail |
| `Left` / `Right` (pager) | Previous / next undeleted mail |
| `i1`..`i9` | Open per-account inbox by account `order` (enabled accounts, order 1-9) |
| `gi` / `gs` / `gd` / `gp` / `gt` | Open current-account inbox / sent / drafts / spam / trash |
| `gb` | Toggle sidebar visibility |
| `gf` | Search sidebar mailboxes |
| `gj` / `gk` | Highlight next / previous sidebar mailbox |
| `gn` / `gN` | Highlight next / previous sidebar mailbox with new mail |
| `go` | Open highlighted sidebar mailbox |
| `gl` | Edit notmuch labels on current message |
| `gL` | Edit notmuch labels, then hide/requery if needed |
| `gU` | Unsubscribe via `List-Unsubscribe` header |
| `gr` | Sync current account (`mail-sync`) and reopen current mailbox |
| `gq` | Prompt for notmuch query virtual folder |
| `gu` | Open message URLs via `urlscan` |

## Neovim

### Global

Source: `private_dot_config/nvim/lua/config/keymaps.lua`.

| Key | Mode | Action |
| --- | --- | --- |
| `Ctrl+H/J/K/L` | n | Window navigation (vim-tmux-navigator compatible) |
| `Ctrl+W h` / `Ctrl+W v` | n | Split side-by-side / stacked (remapped since `Ctrl+H/J/K/L` handle navigation) |
| `Ctrl+S` | n, i | Save file |
| `<leader>fm` | n | Format buffer (conform, async) |

### Diffview

Source: `private_dot_config/nvim/lua/config/keymaps.lua`.

| Key | Action |
| --- | --- |
| `<leader>gd` | Diff branch vs base (auto-detects `main`/`master`/origin HEAD) |
| `<leader>gD` | Diff vs picked branch (Telescope) |
| `<leader>gm` | Open Diffview (index/merge) |
| `<leader>gq` | Close Diffview |
| `Ctrl+/` | Toggle files panel (buffer-local in Diffview) |

### LSP (buffer-local on LspAttach)

Source: `private_dot_config/nvim/lua/plugins/lsp/config.lua`.

| Key | Action |
| --- | --- |
| `gd` / `gD` | Go to definition / declaration |
| `gr` / `gI` / `gy` | Go to references / implementation / type definition |
| `K` | Hover documentation |
| `<leader>ca` | Code action |
| `<leader>rn` | Rename symbol |
| `<leader>d` | Show line diagnostics |
| `<leader>q` | Open diagnostics list |

### Telescope

Source: `private_dot_config/nvim/lua/plugins/telescope.lua`.

| Key | Action |
| --- | --- |
| `<leader>ff` / `<leader>fF` | Find files (filtered / show all) |
| `<leader>fg` / `<leader>fG` | Live grep (filtered / show all) |
| `<leader>fh` | Help tags |
| `<leader>fp` | Zoxide projects (cd on select) |

### Native Config

Source: `private_dot_config/nvim-native/lua/config/keymaps.lua`.

| Key | Action |
| --- | --- |
| `-` | Open the current file's parent directory with Oil |
| `<leader>ff` | Find files with mini.pick |
| `<leader>fg` | Find text with mini.pick and ripgrep |

### Oil (File Explorer)

Source: `private_dot_config/nvim/lua/plugins/oil.lua`. Defaults are disabled (`use_default_keymaps = false`); the buffer-local set is declared explicitly.

| Key | Action |
| --- | --- |
| `<leader>e` | Open Oil (global); close it from inside an Oil buffer |
| `Enter` / `Ctrl+T` / `Ctrl+P` | Select / select in new tab / preview |
| `Ctrl+C` | Close |
| `Ctrl+L` | Refresh |
| `-` / `_` | Parent directory / open cwd |
| `` ` `` / `~` | `cd` (global / tab scope) |
| `gs` / `gx` | Change sort / open external |
| `g.` / `g\` | Toggle hidden / toggle trash |
| `g?` | Show help |

### Bufferline

Source: `private_dot_config/nvim/lua/plugins/bufferline.lua`.

| Key | Action |
| --- | --- |
| `Shift+H` / `Shift+L` | Previous / next buffer |
| `[b` / `]b` | Previous / next buffer |
| `<leader>bp` / `<leader>bP` | Toggle pin / close non-pinned |
| `<leader>bo` | Close other buffers |
| `<leader>bl` / `<leader>bh` | Close buffers to the right / left |
| `<leader>bd` | Delete current buffer |

### Snacks

Source: `private_dot_config/nvim/lua/plugins/snacks.lua`.

| Key | Mode | Action |
| --- | --- | --- |
| `<leader>h` | n | Dashboard |
| `<leader>n` | n | Notification history |
| `<leader>gB` | n | Git browse |
| `<leader>gb` | n | Git blame line |
| `<leader>gf` | n | Lazygit current file history |
| `<leader>gg` | n | Lazygit |
| `<leader>gl` | n | Lazygit log (cwd) |
| `Ctrl+/` | n, t | Toggle terminal |

### Snacks Toggles

Source: `private_dot_config/nvim/lua/plugins/snacks.lua`.

| Key | Toggle |
| --- | --- |
| `<leader>uL` / `<leader>ul` | Relative number / line number |
| `<leader>uc` | Conceal level |
| `<leader>uh` | Inlay hints |
| `<leader>ug` | Indent guides |
| `<leader>uD` | Dim mode |
| `<leader>uw` | Wrap + linebreak |
| `<leader>uv` / `<leader>uV` / `<leader>ux` | Diagnostics / virtual text / underlines |
| `<leader>ua` | Supermaven on/off |
| `<leader>ub` | Bufferline |

### AI

| Key | Mode | Action | Source |
| --- | --- | --- | --- |
| `<leader>ap` | n, v | CodeCompanion actions | `private_dot_config/nvim/lua/plugins/codecompanion.lua` |
| `<leader>ac` | n, v | Toggle AI chat | `private_dot_config/nvim/lua/plugins/codecompanion.lua` |
| `Tab` | i | Accept Supermaven suggestion | `private_dot_config/nvim/lua/plugins/supermaven.lua` |
| `Ctrl+G` | i | Accept Supermaven suggestion word | `private_dot_config/nvim/lua/plugins/supermaven.lua` |
| `Ctrl+]` | i | Clear Supermaven suggestion | `private_dot_config/nvim/lua/plugins/supermaven.lua` |

### Other

| Key | Action | Source |
| --- | --- | --- |
| `<leader>m` | Toggle Markdown preview | `private_dot_config/nvim/lua/plugins/markdown-preview.lua` |
| `<leader>on` / `<leader>os` / `<leader>ot` | Obsidian new note / search / today | `private_dot_config/nvim/lua/plugins/obsidian.lua` |
| `<leader>uu` | Toggle undotree | `private_dot_config/nvim/lua/plugins/undotree.lua` |
| `Escape` | Clear search highlight + dismiss notifications | `private_dot_config/nvim/lua/plugins/noice.lua` |

## Excluded Mappings

The following use plugin-default keymaps and are intentionally excluded from this index:

- **blink.cmp** — default completion keymaps (`keymap = { preset = "default" }`). See `private_dot_config/nvim/lua/plugins/blink.lua`.
- **origami** — default fold keymaps (`foldKeymaps.setup = true`). See `private_dot_config/nvim/lua/plugins/origami.lua`.
- **vim-tmux-navigator** — standard `Ctrl+H/J/K/L` cross-pane navigation.
- **fzf defaults** — stock fzf/fzf-tab behavior beyond the overrides listed above.
