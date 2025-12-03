#!/usr/bin/bash

# Default programs
export EDITOR="nvim"
export VISUAL="nvim"
# export VISUAL="code --user-data-dir ~/.vscode --wait"
export PAGER="bat"

## Path configuration

# Set PATH so it includes user's private bin if it exists
if [[ -d "$HOME/bin" ]]; then
  PATH="$HOME/bin:$PATH"
fi

# Set PATH so it includes user's private bin if it exists
if [[ -d "$HOME/.local/bin" ]]; then
  PATH="$HOME/.local/bin:$PATH"
fi

# Set PATH for dotfiles bin
if [[ -d "$DOTFILES_PATH/bin" ]]; then
  PATH="$DOTFILES_PATH/bin:$PATH"
fi

# Set PATH for cargo bin
if [[ -d "$HOME/.cargo/bin" ]]; then
  PATH="$HOME/.cargo/bin:$PATH"
fi

# Set PATH for postgresql@17
if [[ -d "/opt/homebrew/opt/postgresql@17/bin" ]]; then
  PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
  LDFLAGS="-L/opt/homebrew/opt/postgresql@17/lib"
  CPPFLAGS="-I/opt/homebrew/opt/postgresql@17/include"
fi

## End of path configuration

## Programming language environments

# Python
export PYTHONDONTWRITEBYTECODE=1 # Don't write .pyc files

# Go
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"

# Language preference
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

## End of programming language environments

## Custom environment variables

# Set XDG base directories
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"

# Less settings
export LESS="-R"
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline

# Dotfiles path
export DOTFILES_PATH="$HOME/dev/dotfiles"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Carapace
export CARAPACE_BRIDGES='zsh,fish,bash,inshellisense'

# Nix
export NIX_CONF_DIR="$HOME/.config/nix"

# Opencode
export OPENCODE_CONFIG="$HOME/.config/opencode/opencode.json"

# Zoxide
export _ZO_ECHO=1 # Enable zoxide echo

## End of custom environment variables
