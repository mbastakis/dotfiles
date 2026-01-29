#!/usr/bin/env zsh
# tools.zsh - Tool initializations and shell integrations
# Note: Atuin is loaded in fzf.zsh (after fzf) so it can bind Ctrl+R

# Zoxide - smart cd
if command -v zoxide &>/dev/null; then
  # Unalias zi if it exists (conflicts with zinit)
  (( ${+aliases[zi]} )) && unalias zi
  # Transparent background for zoxide interactive (cdi)
  export _ZO_FZF_OPTS="--color=bg:-1"
  eval "$(zoxide init --cmd cd zsh)"
fi

# Thefuck - command correction (lazy-loaded for faster startup)
if command -v thefuck &>/dev/null; then
  fuck() {
    unfunction fuck  # Remove this wrapper
    eval "$(thefuck --alias)"  # Load the real alias
    fuck "$@"  # Call the real function
  }
fi

# Starship - prompt
command -v starship &>/dev/null && eval "$(starship init zsh)"
