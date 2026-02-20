# Config Overview

Summary of all notable `~/.config/` areas managed by chezmoi, with links to dedicated docs for larger components.

**Source:** `private_dot_config/` -> `~/.config/`

## Managed Components

| Component | Source Path | Dedicated Doc | Description |
|---|---|---|---|
| **Neovim** | `private_dot_config/nvim/` | [nvim.md](nvim.md) | Editor with lazy.nvim, LSP, custom keymaps |
| **OpenCode** | `private_dot_config/opencode/` | [opencode.md](opencode.md) | AI CLI with agents, commands, MCP |
| **Karabiner** | `private_dot_config/private_karabiner/` | [karabiner.md](karabiner.md) | Keyboard remapping (generated config) |
| **Carapace** | `private_dot_config/carapace/` | [carapace.md](carapace.md) | Shell completion framework |
| Ghostty | `private_dot_config/ghostty/` | -- | Terminal emulator |
| tmux | `private_dot_config/tmux/` | -- | Terminal multiplexer |
| Starship | `private_dot_config/starship.toml` | -- | Prompt theme |
| Git | `private_dot_config/git/` | -- | Git config and work profile |
| Bat | `private_dot_config/bat/` | -- | Cat replacement with syntax highlighting |
| Yazi | `private_dot_config/yazi/` | -- | Terminal file manager |
| Lazygit | `private_dot_config/lazygit/` | -- | Git TUI |
| Brew | `private_dot_config/brew/` | -- | Homebrew Brewfile |
| Aerospace | `private_dot_config/aerospace/` | -- | macOS window manager (Darwin only) |
| Finicky | `private_dot_config/finicky/` | -- | macOS browser routing (Darwin only) |
| SketchyBar | `private_dot_config/sketchybar/` | -- | macOS status bar (Darwin only) |
| Raycast | `private_dot_config/raycast/` | -- | macOS launcher (partial, extensions ignored) |
| glab CLI | `private_dot_config/glab-cli/` | -- | GitLab CLI (DT work profile only) |

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
- **Plugins (TPM):** vim-tmux-navigator, catppuccin, tmux-smooth-scroll, tmux-yank, tmux-resurrect, tmux-continuum, tmux-sessionx, tmux-floax, tmux-harpoon
- **Session persistence:** Resurrect + Continuum (auto-save every 15min, restore on start)
- **Status line:** Top position, oasis-style mode indicator with per-mode colors/icons
- **History:** 100,000 lines, mouse enabled, base-index 1

Custom keybindings are documented in [shortcuts.md](../shortcuts.md).

_Reference: `private_dot_config/tmux/tmux.conf:1`_

## Git

Git configuration with optional work profile:

- Base config at `~/.config/git/config`
- Work-specific config at `~/.config/git/.gitconfig-work` (DT work profile only, conditional include)
- Uses delta for diffs (configured in chezmoi config)

_Reference: `private_dot_config/git/`_

## Brew

Homebrew Brewfile at `~/.config/brew/Brewfile`. Managed by the lifecycle script `02-install-packages` which runs `brew bundle` when the Brewfile content changes.

_Reference: `private_dot_config/brew/Brewfile`_

## References

- Neovim AGENTS: `private_dot_config/nvim/AGENTS.md:1`
- OpenCode README: `private_dot_config/opencode/README.md:1`
- Ghostty config: `private_dot_config/ghostty/config:1`
- tmux config: `private_dot_config/tmux/tmux.conf:1`
- Key paths table: `AGENTS.md:78`
