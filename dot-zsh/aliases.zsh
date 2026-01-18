#!/usr/bin/env zsh
# aliases.zsh - Shell aliases

# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Listing
alias l="eza --color=always --icons=always --no-user"
alias ls="eza --color=always --no-user"
alias ll="eza --long --color=always --icons=always --no-user"
alias la="eza --long --color=always --icons=always --no-user --all"
alias ld="eza --long --color=always --no-user --no-permissions --no-filesize --no-time --no-git --group-directories-first --tree"
alias lda="ld --git-ignore --all"
alias lgit="eza --long --git"

# Utilities
alias reload="source ~/.zshrc"

# Vim
alias v="nvim"
alias vi="nvim"
alias vim="nvim"

# Lazygit
alias lg="lazygit"

# Bat
alias b="bat --paging=always --color=always --style=plain --line-range=1:1000 --decorations=always"

# Atuin
alias r="atuin search -i"

# Obsidian CLI
alias obs="obsidian-cli"

# Debug key sequences for zsh
alias keytest="cat -v"

# Opencode
alias oc="OPENCODE_EXPERIMENTAL_PLAN_MODE=1 opencode"
alias ocr="opencode -m amazon-bedrock/anthropic.claude-haiku-4-5-20251001-v1:0 run"
alias oc-restart="launchctl bootout \"gui/$(id -u)/ai.opencode.serve\" 2>/dev/null; launchctl bootstrap \"gui/$(id -u)\" ~/Library/LaunchAgents/ai.opencode.serve.plist && echo 'OpenCode server restarted' && sleep 1 && (tail -20 ~/.local/share/opencode/serve.log 2>/dev/null | grep -E 'listening|error|Error' || echo 'Waiting for logs...')"
alias oc-stop="launchctl bootout \"gui/$(id -u)/ai.opencode.serve\" 2>/dev/null && echo 'OpenCode server stopped' || echo 'OpenCode server was not running'"
alias oc-start="launchctl bootstrap \"gui/$(id -u)\" ~/Library/LaunchAgents/ai.opencode.serve.plist 2>/dev/null && echo 'OpenCode server started' && sleep 1 && (tail -20 ~/.local/share/opencode/serve.log 2>/dev/null | grep -E 'listening|error|Error' || echo 'Waiting for logs...') || echo 'OpenCode server already running'"
alias oc-status="launchctl list | grep ai.opencode.serve || echo 'OpenCode server not running'"
alias oc-logs="tail -f ~/.local/share/opencode/serve.log"

# Ghostty
alias ghostty-settings="nvim ~/.config/ghostty/config"

# Sourcebot (local code search)
alias sb-up="docker-compose -f ~/.config/sourcebot/docker-compose.yml up -d"
alias sb-down="docker-compose -f ~/.config/sourcebot/docker-compose.yml down"
alias sb-logs="docker-compose -f ~/.config/sourcebot/docker-compose.yml logs -f sourcebot"
alias sb-restart="docker-compose -f ~/.config/sourcebot/docker-compose.yml restart sourcebot"
alias sb-status="docker-compose -f ~/.config/sourcebot/docker-compose.yml ps"
alias sb-open="open http://localhost:3000"

# Temporary Commands

## BMAD Method
alias bmad="npx bmad-method"

## SpecKit
alias speckit="uvx --from git+https://github.com/github/spec-kit.git specify"

## Openspec
alias openspec="npx @fission-ai/openspec"
