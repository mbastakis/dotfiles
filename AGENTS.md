# Agent Guidelines for Dotfiles Repository

macOS development environment using Nix Darwin and GNU Stow. All configs symlinked to home directory.

## Repository Structure

| Directory             | Purpose                                              | Symlink Target |
| --------------------- | ---------------------------------------------------- | -------------- |
| `dot-config/`         | App configs (nvim, aerospace, yazi, opencode, etc.)  | `~/.config/`   |
| `dot-zsh/`            | ALL zsh files (aliases, functions, exports, plugins) | `~/.zsh/`      |
| `dot-obsidian/`       | Obsidian plugins, themes, snippets                   | `~/.obsidian/` |
| `dot-bin/`            | User scripts and TUI wrappers                        | `~/.bin/`      |
| `bin/`                | Installation scripts (NOT symlinked)                 | -              |
| `apps/`               | TUI app source code (NOT symlinked)                  | -              |
| `code-portable-data/` | Portable VS Code config                              | -              |

Root dotfiles (`dot-zshrc`, `dot-zshenv`) symlinked directly to `~/` with prefix stripped.

## Build/Lint/Test Commands

### Core Commands

```bash
# Apply Nix configuration (packages, homebrew, system settings)
darwin-rebuild switch --flake .#simple    # Run from dot-config/nix-darwin/

# Apply dotfile symlinks
stow --adopt .                             # Adopt existing files, then stow

# Validate Nix flake
nix flake check                            # Run from dot-config/nix-darwin/

# Reload shell configuration
source ~/.zshrc                            # Or use alias: reload

# Test Neovim config
nvim --headless +q                         # Validates syntax
nvim -c ':checkhealth' -c ':qa'            # Full health check
```

### Utility Scripts

| Script                           | Purpose                                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `./setup.sh`                     | Full setup (Homebrew, Stow, Nix, Yazi plugins, TUI apps, service sync, keyboard layouts, carapace specs) |
| `bin/install_nix.sh`             | Install Nix and apply darwin flake                                                                       |
| `bin/install_code_extensions.sh` | Package and install VS Code extensions                                                                   |
| `dot-bin/nix-add`                | Add brew/cask packages to flake.nix                                                                      |
| `dot-bin/brew-compare`           | Compare Nix-declared vs system-installed packages                                                        |
| `dot-bin/carapace-sync`          | Generate/update carapace completion specs                                                                |

## Code Style Guidelines

### Shell Scripts (dot-zsh/, bin/, setup.sh)

```bash
#!/usr/bin/env bash                    # Preferred shebang (portable)
set -euo pipefail                      # Always use strict mode

# Constants: UPPER_CASE
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'
NC='\033[0m'

# Functions: lowercase_with_underscores
log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Command existence check
command -v brew &>/dev/null || { log_error "brew not found"; exit 1; }

# Conditional sourcing
[[ -f "$file" ]] && source "$file"
```

### Lua/Neovim (dot-config/nvim/)

```lua
-- Indentation: 2 spaces
-- Strings: double quotes preferred
-- Trailing commas in tables

-- Plugin spec (lazy.nvim)
return {
  "author/plugin-name",
  dependencies = { "dep/plugin" },
  opts = {
    option = "value",
  },
}

-- Keymaps
vim.keymap.set("n", "<leader>key", func, { desc = "Description" })

-- LSP customization (in after/lsp/*.lua)
vim.lsp.config("server_name", {
  settings = { ... },
})
```

### Nix (dot-config/nix-darwin/flake.nix)

```nix
# Packages in double quotes, alphabetically sorted
homebrew.brews = [
  "awscli"
  "bat"
  "fzf"
];

# Tap packages include tap prefix
"oven-sh/bun/bun"
```

### Python

Always use `uv` for environment creation and script execution:

```bash
uv venv .venv
uv pip install package
uv run script.py
uvx tool-name     # Run tools without installing
```

### Config Files (YAML, TOML)

- **Indentation**: 2 spaces
- **Theme**: Catppuccin Mocha colors throughout
- **Section separators**: Blank lines between major sections

## Naming Conventions

| Type               | Convention                   | Example                    |
| ------------------ | ---------------------------- | -------------------------- |
| Shell functions    | `lowercase_with_underscores` | `log_info`, `git_pull_all` |
| Shell constants    | `UPPER_CASE`                 | `SCRIPT_DIR`, `RED`        |
| Config directories | `dot-config/tool-name/`      | `dot-config/nvim/`         |
| Zsh modules        | `dot-zsh/name.zsh`           | `dot-zsh/aliases.zsh`      |
| Lua plugins        | `lua/plugins/feature.lua`    | `lua/plugins/linting.lua`  |

## Error Handling

### Shell Scripts

```bash
set -euo pipefail                          # Exit on error, undefined vars, pipe failures
command -v tool &>/dev/null || exit 1      # Check command exists
[[ -d "$dir" ]] || { echo "Not found"; exit 1; }
```

### Logging Pattern

Use colored output with severity prefixes:

- `[INFO]` (green) - Progress messages
- `[WARNING]` (yellow) - Non-fatal issues
- `[ERROR]` (red, to stderr) - Fatal errors

## Theme: Catppuccin Mocha

Used consistently across all tools. Key colors:

```
base     = "#1e1e2e"    text     = "#cdd6f4"
red      = "#f38ba8"    green    = "#a6e3a1"
yellow   = "#f9e2af"    blue     = "#89b4fa"
mauve    = "#cba6f7"    peach    = "#fab387"
```

## Important Notes

- **Zsh files**: ALL go in `dot-zsh/`, NOT `dot-config/`
- **Stow ignore**: See `.stow-local-ignore` for excluded files; AGENTS.md files auto-ignored via `**/AGENTS.md`
- **Stow uses Perl regex**: `.stow-local-ignore` patterns are Perl regex, not globs. Use `node_modules` not `**/node_modules`; escape dots like `bun\.lock`
- **Stow --adopt gotcha**: If home directory has symlinks pointing INTO the repo (e.g., `~/foo -> ~/dev/dotfiles/apps/foo`), `stow --adopt` creates those symlinks in repo root. Delete unexpected root symlinks after adopt.
- **Wrapper scripts need stow first**: Scripts in `dot-bin/` referencing `~/.config/` paths fail until `stow --adopt .` creates symlinks
- **Git config**: Uses conditional includes for work/personal based on repo path
- **Local overrides**: Put machine-specific config in `dot-zsh/local.zsh` (gitignored)
- **API keys**: Store in `dot-zsh/local.zsh`, never commit secrets

## OpenTUI Apps

TUI applications in `apps/` use OpenTUI React (source NOT symlinked, wrappers in `dot-bin/`):

| App             | Location                | Alias | Purpose                               |
| --------------- | ----------------------- | ----- | ------------------------------------- |
| nix-manager     | `apps/nix-manager/`     | -     | Manage Homebrew vs Nix flake packages |
| service-manager | `apps/service-manager/` | `svc` | Manage macOS services                 |

**Pattern**: Both apps share same architecture (Header, List, StatusBar, DetailPanel) and Catppuccin theme. Use as reference for new TUI tools.
