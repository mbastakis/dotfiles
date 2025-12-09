#!/usr/bin/env zsh
# tools.zsh - Tool initializations and shell integrations

# Atuin - shell history
command -v atuin &>/dev/null && eval "$(atuin init zsh)"

# Zoxide - smart cd
if command -v zoxide &>/dev/null; then
  # Unalias zi if it exists (conflicts with zinit)
  (( ${+aliases[zi]} )) && unalias zi
  eval "$(zoxide init --cmd cd zsh)"
fi

# Thefuck - command correction
command -v thefuck &>/dev/null && eval "$(thefuck --alias)"

# Starship - prompt
command -v starship &>/dev/null && eval "$(starship init zsh)"
