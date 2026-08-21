#!/usr/bin/env zsh
# aliases.zsh - Shell aliases

# Navigation
alias ..="cd .."
alias grt='cd "$(git rev-parse --show-toplevel || echo .)"'

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
alias v="NVIM_APPNAME=nvim-native nvim"
alias vi="nvim"
alias vim="nvim"

# Lazygit
alias lg="lazygit"

# Bat
alias b="bat --paging=always --color=always --style=plain --line-range=1:1000 --decorations=always"

# Obsidian CLI
alias obs="obsidian"

# Mail
alias nm="neomutt"
alias msync="mail-sync"
alias ab='abook --config "$XDG_CONFIG_HOME/abook/abookrc" --datafile "$XDG_DATA_HOME/abook/addressbook"'

# Kubernetes
alias k="kubectl"
alias ctx="kubectx"
alias ns="kubens"

# Ghostty
alias ghostty-settings="nvim ~/.config/ghostty/config"

# Chezmoi
alias cz="chezmoi"

# Taskwarrior — `taskwarrior-tui` shells out to a `task` binary internally,
# and Homebrew re-prepends /opt/homebrew/bin ahead of ~/bin in .zshrc, so
# name-shadowing via PATH order alone isn't reliable. Alias to the ~/bin
# wrapper explicitly so it always wins for interactive use.
alias taskwarrior-tui="$HOME/bin/taskwarrior-tui"

# Tmux
alias ta="tmux attach"
alias td="tmux detach"
alias tls="tmux ls"

# Opencode
alias oc="opencode-launch"
alias ocm="opencode-launch mini"
alias occ="opencode-launch --continue"
alias ocserve="opencode-server"

# Lazyssh
alias lssh="lazyssh"

# Python
alias python="python3"
