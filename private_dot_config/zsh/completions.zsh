#!/usr/bin/env zsh
# completions.zsh - Tool-specific completions

# Register repo-owned native completion functions explicitly so they are
# available even while compinit is using a fresh cached dump.
autoload -Uz _add-zoxide-tree _aws-login _starship-timer
compdef _add-zoxide-tree add-zoxide-tree
compdef _aws-login aws-login aws-login-exec
compdef _starship-timer starship-timer

# AWS CLI ships a bash completer; register it through bashcompinit.
if command -v aws_completer &>/dev/null; then
  autoload -Uz bashcompinit
  bashcompinit
  complete -C "$(command -v aws_completer)" aws
fi

# Cache OpenCode's native completion output until the binary changes.
if command -v opencode &>/dev/null; then
  _opencode_cache="$ZSH_COMPLETION_CACHE_DIR/opencode-completion.zsh"
  _opencode_bin="$(command -v opencode)"
  _opencode_tmp="$_opencode_cache.tmp.$$"

  if [[ ! -f "$_opencode_cache" || ! -s "$_opencode_cache" || "$_opencode_bin" -nt "$_opencode_cache" ]]; then
    if opencode completion >|"$_opencode_tmp" 2>/dev/null; then
      mv "$_opencode_tmp" "$_opencode_cache"
    else
      rm -f "$_opencode_tmp"
    fi
  fi

  [[ -f "$_opencode_cache" ]] && source "$_opencode_cache"
  unset _opencode_cache _opencode_bin _opencode_tmp
fi

# Cache sesh's native completion output until the binary changes.
if command -v sesh &>/dev/null; then
  _sesh_cache="${XDG_CACHE_HOME:-$HOME/.cache}/sesh-completion.zsh"
  _sesh_bin="$(command -v sesh)"
  _sesh_tmp="$_sesh_cache.tmp.$$"

  if [[ ! -f "$_sesh_cache" || ! -s "$_sesh_cache" || "$_sesh_bin" -nt "$_sesh_cache" ]]; then
    mkdir -p "${XDG_CACHE_HOME:-$HOME/.cache}"
    if sesh completion zsh >|"$_sesh_tmp" 2>/dev/null; then
      mv "$_sesh_tmp" "$_sesh_cache"
    else
      rm -f "$_sesh_tmp"
    fi
  fi

  [[ -f "$_sesh_cache" ]] && source "$_sesh_cache"
  unset _sesh_cache _sesh_bin _sesh_tmp
fi
