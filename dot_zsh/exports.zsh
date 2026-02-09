#!/usr/bin/env zsh
# exports.zsh - Environment variables for interactive use
# (PATH, EDITOR, XDG, etc. are in ~/.zshenv for all shell types)

# Pager
export PAGER="bat"

# Less settings and colors
export LESS="-R"
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline

# Carapace completion bridges
export CARAPACE_BRIDGES='zsh,fish,bash,inshellisense'

# Zoxide echo (show directory after cd)
export _ZO_ECHO=1

# Ripgrep config
export RIPGREP_CONFIG_PATH="$HOME/.config/ripgrep/config"

# OpenCode Exa integration (enables websearch/codesearch tools)
# export OPENCODE_ENABLE_EXA=true

# Zellij auto-start behavior
export ZELLIJ_AUTO_ATTACH="true"
export ZELLIJ_AUTO_SESSION_NAME="test-setup"
export ZELLIJ_AUTO_SESSION_LAYOUT="$HOME/.config/zellij/layout/test-setup.kdl"
