# Config Overview

Summary of notable config areas managed by chezmoi, with links to dedicated docs for larger components.

**Source:** `private_dot_config/` -> `~/.config/`, `private_dot_local/private_share/` -> `~/.local/share/`

## Managed Components

| Component | Source Path | Dedicated Doc | Description |
|---|---|---|---|
| **Neovim** | `private_dot_config/nvim/` | [nvim.md](nvim.md) | Editor with lazy.nvim, LSP, custom keymaps |
| **OpenCode** | `private_dot_config/opencode/` | [opencode.md](opencode.md) | Primary AI CLI profile with agents, commands, and skills |
| **OpenCode OMO** | `private_dot_config/opencode-omo/` | [opencode.md](opencode.md) | Isolated OpenCode profile reserved for `oh-my-openagent` |
| **Karabiner** | `private_dot_config/private_karabiner/` | [karabiner.md](karabiner.md) | Keyboard remapping (generated config) |
| **Carapace** | `private_dot_config/carapace/` | [carapace.md](carapace.md) | Shell completion framework |
| **Zsh** | `private_dot_config/zsh/`, `dot_zshenv.tmpl` | [zsh.md](zsh.md) | Shell bootstrap plus XDG-aware tool/runtime environment |
| **Atuin** | `private_dot_config/private_atuin/private_config.toml` | -- | Shell history search, sync, and AI settings |
| Vim | `private_dot_config/vim/vimrc` | -- | Minimal Vim config that redirects state into XDG paths |
| Terraform CLI | `private_dot_config/terraform/terraform.rc` | -- | CLI defaults (for example checkpoint suppression) |
| **NeoMutt** | `private_dot_config/neomutt/` | [email.md](email.md) | Terminal mail client config and custom mailbox bindings |
| **notmuch** | `private_dot_config/notmuch/default/` | [email.md](email.md) | Mail index/search config and tagging hook |
| **msmtp** | `private_dot_config/msmtp/private_config.tmpl` | [email.md](email.md) | SMTP account config rendered from Bitwarden secrets |
| **isync (mbsync)** | `private_dot_config/isyncrc.tmpl` | [email.md](email.md) | IMAP sync channels and Maildir mapping |
| **abook** | `private_dot_config/abook/`, `private_dot_local/private_share/abook/` | [email.md](email.md) | Local address book split across XDG config/data paths |
| Colima | `private_dot_local/private_share/colima/` | -- | Container runtime config and VM state |
| Mise | `private_dot_config/mise/` | -- | Tool/version manager config (`linear-cli`) |
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
| Diffnav | `private_dot_config/diffnav/` | -- | Git diff TUI pager (file tree + delta rendering) |
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
- Uses diffnav as `git diff`/`git show` pager (TUI with file tree, powered by delta underneath)
- Delta remains as `core.pager` for non-diff git output (log, blame) and as interactive diffFilter
- Catppuccin Mocha theme via delta's `[delta]` config section

_Reference: `private_dot_config/git/`_

## Brew

Homebrew Brewfile at `~/.config/brew/Brewfile`. Managed by the lifecycle script `02-install-packages` which runs `brew bundle` when the Brewfile content changes.

`aws-login` is installed from the private tap `mbastakis/tap` (formula `mbastakis/tap/aws-login`) instead of being compiled from dotfiles source.

_Reference: `private_dot_config/brew/Brewfile`_

## References

- Neovim AGENTS: `private_dot_config/nvim/AGENTS.md:1`
- OpenCode README: `private_dot_config/opencode/README.md:1`
- Email stack doc: `docs/components/email.md:1`
- mbsync template: `private_dot_config/isyncrc.tmpl:1`
- Ghostty config: `private_dot_config/ghostty/config:1`
- tmux config: `private_dot_config/tmux/tmux.conf:1`
- Key paths table: `AGENTS.md:78`
