# Agent Guidelines for Dotfiles Repository

## Repository Structure
- **bin/**: Installation scripts (Nix, VS Code extensions)
- **dot-zsh/**: Zsh configuration modules (aliases, functions, exports, plugins, fzf, fzf-tab) sourced by dot-zshrc. ALL .zsh files belong here, not in dot-config/
- **dot-config/**: Application configurations for tools that use ~/.config/ (nix-darwin, nvim, aerospace, sketchybar, carapace, etc.) symlinked to ~/.config/
- **dot-claude/**: Claude AI integration (commands, hooks, plugins) symlinked to ~/.claude/
- **dot-obsidian/**: Obsidian vault configuration (plugins, themes, snippets) symlinked to ~/.obsidian/
- **dot-warp/**: Warp terminal workflows and themes symlinked to ~/.warp/
- **code-portable-data/**: Portable VS Code configuration and extensions
- Root dotfiles (dot-zshrc, dot-gitconfig, etc.) are symlinked directly to ~/ by Stow

**Important**: Zsh-specific configs (.zsh files) go in dot-zsh/, NOT dot-config/. Only tools that explicitly use ~/.config/ belong in dot-config/

## Completion System
The shell uses a **Carapace + fzf-tab** completion stack:
1. **Carapace** provides completions for 1000+ commands (aws, kubectl, docker, git, npm, etc.) via the zsh completion system
2. **fzf-tab** intercepts zsh completions and displays them in an interactive fzf interface
3. **Catppuccin Mocha** theme provides consistent styling

**Integration flow:**
- `carapace _carapace` registers all carapace completers with zsh via `compdef`
- When you press TAB, zsh calls the registered completer function
- Carapace generates the completion suggestions dynamically
- fzf-tab intercepts the completion list before display
- You see an interactive, searchable fzf interface with previews

**To verify it's working:** After reloading shell, type `aws <TAB>` or `kubectl <TAB>` - you should see an interactive fzf menu with completions provided by carapace

## Build/Lint/Test Commands
- **Apply Nix Darwin changes**: `cd dot-config/nix-darwin && darwin-rebuild switch --flake .#simple`
- **Apply Stow symlinks**: `stow .` (from repo root)
- **Validate Nix flake**: `nix flake check` (from dot-config/nix-darwin/)
- **Reload shell config**: `source ~/.zshrc` or `reload`
- **No test suite**: This is a configuration repository; validate by testing actual tool behavior

## Code Style Guidelines

### Shell Scripts (.sh, .zsh)
- Use `#!/usr/bin/env sh` or `#!/bin/bash` for portability
- Follow existing function naming conventions (lowercase with underscores)
- Use descriptive variable names with consistent casing
- Add comments for complex logic, especially in custom functions
- Prefer long-form flags for readability (e.g., `--all` over `-a`)

### Configuration Files
- Maintain consistent indentation (tabs in shell configs, spaces elsewhere)
- Follow tool-specific conventions (e.g., Lua uses 2-space indents per .stylua.toml)
- Use Catppuccin Mocha theme colors across all configs for consistency
- Preserve existing commenting style within each file type

### Naming Conventions
- Configuration directories: `dot-config/tool-name/` for tools using ~/.config/
- Zsh configuration files: `dot-zsh/name.zsh` for all shell-specific configs
- Custom aliases: lowercase, descriptive (e.g., `reload`, `brew_update`)
- Functions: lowercase_with_underscores (e.g., `check_repos_behind`)
- Zsh configs are sourced at the end of dot-zshrc in this order: local.zsh, plugins.zsh, aliases.zsh, functions.zsh, custom_shortcuts.zsh, obsidian-cli.zsh, fzf.zsh

### Error Handling
- Use `set -euo pipefail` in critical setup scripts
- Provide user-friendly error messages with log functions (log_info, log_error, log_warning)
- Validate prerequisites before performing operations
