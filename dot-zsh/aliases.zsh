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
alias reload="exec zsh" # Replace shell with fresh instance
alias r="reload"
alias zsh-profile="ZSHRC_PROFILE=1 zsh -i -c exit"
alias zsh-time="time (zsh -i -c exit)"

# Vim
alias v="nvim"
alias vi="nvim"
alias vim="nvim"

# Lazygit
alias lg="lazygit"

# Bat
alias b="bat --paging=always --color=always --style=plain --line-range=1:1000 --decorations=always"

# Atuin
# alias r="atuin search -i"  # Use ctrl+r instead

# Obsidian CLI
alias obs="obsidian-cli"

# Debug key sequences for zsh
alias keytest="cat -v"

# Kubernetes
alias ctx="kubectx"

# Ghostty
alias ghostty-settings="nvim ~/.config/ghostty/config"
