#!/usr/bin/bash

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
alias oc="opencode"
alias ocr="opencode -m amazon-bedrock/anthropic.claude-haiku-4-5-20251001-v1:0 run"

# Ghostty
alias ghostty-settings="nvim ~/.config/ghostty/config"

# Temporary Commands

## BMAD Method
alias bmad="npx bmad-method"

## SpecKit
alias speckit="uvx --from git+https://github.com/github/spec-kit.git specify"

## Openspec
alias openspec="npx @fission-ai/openspec"
