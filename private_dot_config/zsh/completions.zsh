#!/usr/bin/env zsh
# completions.zsh - Tool-specific completions

# Aggregated completions (optional; disabled by default in carapace.zsh)
source "$ZDOTDIR/carapace.zsh"

# Cache sesh's native completion so it works even when carapace is disabled.
if command -v sesh &>/dev/null; then
  _sesh_cache="${XDG_CACHE_HOME:-$HOME/.cache}/sesh-completion.zsh"
  _sesh_bin="$(command -v sesh)"
  _sesh_tmp="$_sesh_cache.tmp"

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
