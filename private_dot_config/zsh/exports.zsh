#!/usr/bin/env zsh
# exports.zsh - Environment variables for interactive use
# (PATH, EDITOR, XDG, etc. are in ~/.zshenv for all shell types)

# Pager — disable rich pagers in agent/non-TTY contexts.
# OpenCode sets OPENCODE=1; its Bash tool uses piped stdout (no PTY).
if [[ -n "${OPENCODE:-}" ]] || [[ ! -t 1 ]]; then
  export PAGER="cat"
  export GIT_PAGER="cat"
  export BAT_PAGER=""
  export MANPAGER="cat"
else
  export PAGER="bat"
fi

# Less settings and colors
export LESS="-R"
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline

# Carapace completions (aws, kubectl, docker, etc.)
# Enabled by default. Set this to 0 here if you want to disable the loader.
export ZSH_ENABLE_CARAPACE=1
export CARAPACE_BRIDGES='zsh,fish,bash,inshellisense'

# Zoxide echo (show directory after cd)
export _ZO_ECHO=1

# OpenCode
export OPENCODE_CONFIG="$HOME/.config/opencode/opencode.jsonc"
export OPENCODE_CONFIG_DIR="$HOME/.config/opencode"
