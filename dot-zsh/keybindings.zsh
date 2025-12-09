#!/usr/bin/env zsh
# keybindings.zsh - Custom keybindings
# Note: shift-select bindings are loaded via zinit in plugins.zsh

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
  bindkey '^G' navi_widget
fi

# ftext - ripgrep search with fzf preview (Ctrl-F)
# Requires ftext function from functions.zsh
zle -N ftext-widget
bindkey '^F' ftext-widget

# Zoxide interactive selection (Alt-C)
function run_zoxide_interactive() {
  BUFFER="cdi"
  zle accept-line
}
zle -N run_zoxide_interactive
bindkey '\ec' run_zoxide_interactive
