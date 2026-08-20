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

# ftext - ripgrep search with fzf preview (Ctrl-F)
# Requires ftext function from functions.zsh
zle -N ftext-widget
for _map in "${_widget_bind_maps[@]}"; do
  bindkey -M "$_map" '^F' ftext-widget
done

# fzf directory picker (Ctrl-Shift-T via Ghostty sequence)
# Uses fzf-file-widget with a temporary directory-only source.
function fzf-directory-widget() {
  (( $+widgets[fzf-file-widget] )) || return 0

  local dir_command="${FZF_CTRL_SHIFT_T_COMMAND:-${FZF_CTRL_T_COMMAND:-}}"
  local dir_opts="${FZF_CTRL_SHIFT_T_OPTS:-${FZF_CTRL_T_OPTS:-}}"
  local FZF_CTRL_T_COMMAND="$dir_command"
  local FZF_CTRL_T_OPTS="$dir_opts"

  zle fzf-file-widget
}
zle -N fzf-directory-widget
for _map in "${_widget_bind_maps[@]}"; do
  bindkey -M "$_map" '^[[202~' fzf-directory-widget
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

# Worktrunk worktree picker (Cmd-B via Ghostty ESC[203~ passthrough).
# Runs in the invoking shell so wt's shell integration can cd to the selection.
if command -v wt &>/dev/null; then
  function wt-switch-widget() {
    BUFFER="wt switch"
    zle accept-line
  }
  zle -N wt-switch-widget
  for _map in "${_widget_bind_maps[@]}"; do
    bindkey -M "$_map" '^[[203~' wt-switch-widget
  done
fi

# Accept autosuggestion one word at a time.
# zsh-autosuggestions already treats forward-word as partial accept.

# Alt/Option combinations are escape-prefixed. A larger timeout helps zsh
# read the full sequence instead of treating bare Esc as vi-cmd-mode.
(( KEYTIMEOUT < 80 )) && KEYTIMEOUT=80

typeset -a _word_fwd_keys _word_back_keys
_word_fwd_keys=('^[f' '^[[1;3C' '^[[1;5C' '^[[1;9C' '^[[5C')
_word_back_keys=('^[b' '^[[1;3D' '^[[1;5D' '^[[1;9D' '^[[5D')

typeset -a _line_home_keys _line_end_keys
_line_home_keys=('^[[1~' '^[[H' '^[OH')
_line_end_keys=('^[[4~' '^[[F' '^[OF')

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

# Home/End key sequences (including Cmd+Left/Cmd+Right from Ghostty).
for _seq in "${_line_home_keys[@]}"; do
  bindkey -M emacs "$_seq" beginning-of-line
  bindkey -M viins "$_seq" beginning-of-line
  bindkey -M vicmd "$_seq" vi-beginning-of-line
done
for _seq in "${_line_end_keys[@]}"; do
  bindkey -M emacs "$_seq" end-of-line
  bindkey -M viins "$_seq" end-of-line
  bindkey -M vicmd "$_seq" vi-end-of-line
done

unset _seq _map _word_fwd_keys _word_back_keys _line_home_keys _line_end_keys _widget_bind_maps

# Keep line editor in emacs mode and disable Esc -> vi-cmd-mode switching.
bindkey -e

# Atuin installs the AI widget in the active map during init. Rebind it after
# selecting emacs mode so ? opens AI and Tab can return a command to LBUFFER.
if (( $+widgets[self-atuin-ai-question-mark] )); then
  bindkey -M emacs '?' self-atuin-ai-question-mark
  bindkey -M viins '?' self-atuin-ai-question-mark
fi
