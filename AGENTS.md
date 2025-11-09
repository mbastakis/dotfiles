# Agent Guidelines for Dotfiles Repository

## Repository Structure
- **dot-zsh/**: Zsh configs (aliases, functions, exports, plugins). ALL .zsh files go here, NOT dot-config/
- **dot-config/**: App configs for ~/.config/ tools (nix-darwin, nvim, aerospace, yazi, etc.)
- **dot-claude/**, **dot-obsidian/**, **dot-warp/**: AI, knowledge base, and terminal configs
- **code-portable-data/**: Portable VS Code configuration
- Root dotfiles symlinked by Stow to ~/ (dot-zshrc → ~/.zshrc)

## Build/Lint/Test Commands
- **Apply Nix changes**: `cd dot-config/nix-darwin && darwin-rebuild switch --flake .#simple`
- **Apply symlinks**: `stow .` (from repo root)
- **Validate Nix**: `nix flake check` (from dot-config/nix-darwin/)
- **Reload shell**: `source ~/.zshrc` or `reload`
- **Test completions**: `aws <TAB>` or `kubectl <TAB>` should show fzf menu

## Code Style
- **Shell scripts**: Use `#!/usr/bin/env sh` or `#!/bin/bash`, lowercase_with_underscores for functions/variables, long-form flags for clarity
- **Config files**: Maintain existing indentation (tabs for shell, spaces elsewhere), use Catppuccin Mocha theme colors
- **Naming**: `dot-config/tool-name/` for ~/.config tools, `dot-zsh/name.zsh` for shell configs
- **Zsh load order**: local.zsh → plugins.zsh → aliases.zsh → functions.zsh → custom_shortcuts.zsh → obsidian-cli.zsh → fzf.zsh
- **Error handling**: Use `set -euo pipefail`, provide user-friendly messages with log_info/log_error/log_warning functions
