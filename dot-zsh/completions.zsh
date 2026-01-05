#!/usr/bin/env zsh
# completions.zsh - Tool completions
# Loaded AFTER compinit (which runs in plugins.zsh)

# Bun completions
[[ -s "$HOME/.bun/_bun" ]] && source "$HOME/.bun/_bun"

# Obsidian CLI completions
command -v obsidian-cli &>/dev/null && eval "$(obsidian-cli completion zsh)"

# OpenCode completions
command -v opencode &>/dev/null && eval "$(opencode completion)"
