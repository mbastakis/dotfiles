# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a macOS dotfiles repository using **Nix Darwin** for declarative package management and **GNU Stow** for symlink-based configuration management. The setup is designed for an AI-first development workflow with extensive terminal integration.

## Core Architecture

### Configuration Management System

The repository uses a two-layer configuration approach:

1. **Nix Darwin** (`dot-config/nix-darwin/flake.nix`): Manages system packages, Homebrew formulas/casks, and macOS system preferences
2. **GNU Stow**: Creates symlinks from `dot-*` directories to `~` (e.g., `dot-config/` → `~/.config/`)

The `.stowrc` file configures Stow with `--dotfiles` flag, which means files/directories prefixed with `dot-` are symlinked with a `.` prefix in the home directory.

### Directory Naming Convention

All configuration directories use the `dot-` prefix and are symlinked via Stow:
- `dot-config/` → `~/.config/`
- `dot-zsh/` → `~/.zsh/`
- `dot-claude/` → `~/.claude/`
- `dot-zshrc` → `~/.zshrc`
- `dot-gitconfig` → `~/.gitconfig`

### Modular Zsh Configuration

The shell environment (`dot-zshrc`) sources configuration modules in this order:
1. `~/.zshenv` - Environment variables
2. `~/.zsh/local.zsh` - Machine-specific settings (not tracked, created on setup)
3. `~/.zsh/plugins.zsh` - Zinit plugin manager configuration
4. `~/.zsh/aliases.zsh` - Command aliases
5. `~/.zsh/functions.zsh` - Shell functions
6. `~/.zsh/custom_shortcuts.zsh` - Custom keybindings
7. `~/.zsh/obsidian-cli.zsh` - Obsidian CLI integration
8. `~/.zsh/fzf.zsh` - FZF fuzzy finder configuration
9. `~/.zsh/fzf-tab.zsh` - Interactive tab completions with FZF

### Git Configuration

Git uses conditional includes based on repository location:
- `~/dev/work/` repos use `~/.gitconfig-work`
- `~/dev/personal/` repos use `~/.gitconfig-personal`

The main config uses delta as the pager with Catppuccin Mocha theme and zdiff3 merge conflict style.

## Common Commands

### Initial Setup

```bash
# Run automated setup (installs Homebrew, Stow, Nix)
./setup.sh

# Apply Nix Darwin configuration (from dot-config/nix-darwin/)
cd dot-config/nix-darwin
darwin-rebuild switch --flake .#simple

# Install VS Code extensions
./bin/install_code_extensions.sh
```

### Package Management

```bash
# Rebuild system configuration after editing flake.nix
cd dot-config/nix-darwin
darwin-rebuild switch --flake .#simple

# Compare Nix-declared vs system-installed packages
./utils/brew-compare.sh

# Update Nix flake inputs
nix flake update dot-config/nix-darwin

# Search for Nix packages
nix-env -qaP | bat
```

### Stow Operations

```bash
# Re-apply all symlinks from repository root
stow .

# Remove all symlinks
stow -D .

# Simulate stow operation (dry-run)
stow -n .
```

### Adding New Packages

When adding packages to `dot-config/nix-darwin/flake.nix`:

1. **For Nix packages**: Add to `environment.systemPackages` array
2. **For Homebrew formulas**: Add to `homebrew.brews` array
3. **For Homebrew casks (GUI apps)**: Add to `homebrew.casks` array
4. **For Mac App Store apps**: Add to `homebrew.masApps` with app ID
5. Rebuild: `darwin-rebuild switch --flake .#simple`
6. Verify: `./utils/brew-compare.sh`

### Shell Configuration Changes

After modifying any `dot-zsh/*.zsh` file:
```bash
source ~/.zshrc
# Or use the alias: reload
```

## AI Integration

### OpenCode Configuration

OpenCode config is at `dot-config/opencode/opencode.json` with MCP servers:
- **snap-happy**: Screenshot capture tool
- **context7**: Code context management
- **mcp-obsidian**: Obsidian knowledge base integration
- **sequential-thinking**: Enhanced reasoning capabilities

OpenCode has custom permission rules for specific bash commands and auto-allows edit operations.

### Claude Code Setup

Custom commands are in `dot-claude/commands/`:
- `add_warp_workflow.md` - Create Warp terminal workflows
- `context_prime.md` - Context priming for conversations
- `create_worktrees.md` - Git worktree management
- `infinite.md` - Extended conversation mode

## Key Development Tools

### Shell & Terminal
- **Zsh** with **Zinit** plugin manager
- **Starship** prompt (config at `dot-config/starship.toml`)
- **Carapace** for 1000+ command completions
- **fzf-tab** for interactive fuzzy tab completions
- **Atuin** for shell history sync
- **Zoxide** for directory jumping (aliased to `cd`)

### File & Git Tools
- **Yazi** file manager (config at `dot-config/yazi/`)
- **Lazygit** TUI (config at `dot-config/lazygit/`)
- **Delta** diff viewer with Catppuccin theme
- **gh** (GitHub CLI) and **glab** (GitLab CLI)

### Development
- **Neovim** using Kickstart config (at `dot-config/nvim/`)
- **Docker** with **Colima**, **Lazydocker**, and **ctop**
- **Kubernetes** with **kubectl**, **kubectx**, **k9s**, **helm**
- **Cloud**: **awscli**, **azure-cli**, **terraform**
- **Languages**: Node, Bun, Go, Rust, Python (uv/pyenv), Java, Lua

### Window Management
- **AeroSpace** tiling window manager (config at `dot-config/aerospace/`)
  - Dvorak-optimized keybindings
- **SketchyBar** menu bar (config at `dot-config/sketchybar/`)

## Important Notes

### Nix Darwin Configuration
The main system configuration is the `simple` profile in `flake.nix`. It declares:
- System packages via Nix
- Homebrew packages (formulas, casks, Mac App Store apps)
- macOS system preferences (dock, finder, etc.)

The flake uses `nixpkgs-unstable` and follows the latest `nix-darwin` master branch.

### Stow Behavior
- Stow creates symlinks, not copies
- The `--dotfiles` flag transforms `dot-` prefix to `.` in the target directory
- Target is `~` (home directory) as specified in `.stowrc`
- Stow is verbose (`-v` flag) by default

### Shell Completions
The setup uses **both** Carapace and fzf-tab:
- **Carapace** provides completion specs for 1000+ commands
- **fzf-tab** presents completions in an interactive fuzzy finder menu
- Zsh's built-in completion system (`compinit`) is enabled

### Catppuccin Mocha Theme
System-wide theme preference. Relevant configs:
- Git delta: `~/.config/delta/themes/catppuccin.gitconfig`
- Starship: defined in `dot-config/starship.toml`
- Various tool configs in `dot-config/`

### API Keys & Secrets
Machine-specific secrets go in `~/.zsh/local.zsh` (not tracked in git). See `dot-zsh/local.zsh.example` for reference structure.

### Primary User
The system user is `mbastakis` as declared in `flake.nix` (`system.primaryUser`).
