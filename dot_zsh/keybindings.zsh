#!/usr/bin/env zsh
# keybindings.zsh - Custom keybindings
# Note: shift-select bindings are loaded via zinit in plugins.zsh

typeset -a _widget_bind_maps
_widget_bind_maps=(emacs viins vicmd main)

# Insert a literal newline in the command buffer (multiline edit) without executing.
function insert-literal-newline() {
  LBUFFER+=$'\n'
}
zle -N insert-literal-newline
for _map in "${_widget_bind_maps[@]}"; do
  bindkey -M "$_map" '^J' insert-literal-newline
done

# Navi cheatsheet widget (Ctrl-G)
if command -v navi &>/dev/null; then
  function navi_widget() {
    local result
    result="$(navi --print)"
    if [[ -n "$result" ]]; then
      LBUFFER="$result"
    fi
    zle reset-prompt
  }
  zle -N navi_widget
  for _map in "${_widget_bind_maps[@]}"; do
    bindkey -M "$_map" '^G' navi_widget
  done
fi

# ftext - ripgrep search with fzf preview (Ctrl-F)
# Requires ftext function from functions.zsh
zle -N ftext-widget
for _map in "${_widget_bind_maps[@]}"; do
  bindkey -M "$_map" '^F' ftext-widget
done

# Zoxide interactive selection (Ctrl-Z)
function run_zoxide_interactive() {
  BUFFER="cdi"
  zle accept-line
}
zle -N run_zoxide_interactive
for _map in "${_widget_bind_maps[@]}"; do
  bindkey -M "$_map" '^Z' run_zoxide_interactive
done

# Accept autosuggestion one word at a time.
# zsh-autosuggestions already treats forward-word as partial accept.

# Alt/Option combinations are escape-prefixed. A larger timeout helps zsh
# read the full sequence instead of treating bare Esc as vi-cmd-mode.
(( KEYTIMEOUT < 80 )) && KEYTIMEOUT=80

typeset -a _word_fwd_keys _word_back_keys
_word_fwd_keys=('^[f' '^[[1;3C' '^[[1;5C' '^[[1;9C' '^[[5C')
_word_back_keys=('^[b' '^[[1;3D' '^[[1;5D' '^[[1;9D' '^[[5D')

# Insert mode: use emacs word movement so autosuggest partial-accept is stable.
for _seq in "${_word_fwd_keys[@]}"; do
  bindkey -M emacs "$_seq" emacs-forward-word
  bindkey -M viins "$_seq" emacs-forward-word
done
for _seq in "${_word_back_keys[@]}"; do
  bindkey -M emacs "$_seq" emacs-backward-word
  bindkey -M viins "$_seq" emacs-backward-word
done

# Command mode fallback (if Esc already switched keymap).
for _seq in "${_word_fwd_keys[@]}"; do
  bindkey -M vicmd "$_seq" vi-forward-word-end
done
for _seq in "${_word_back_keys[@]}"; do
  bindkey -M vicmd "$_seq" vi-backward-word
done

unset _seq _map _word_fwd_keys _word_back_keys _widget_bind_maps

# Keep line editor in emacs mode and disable Esc -> vi-cmd-mode switching.
bindkey -e
