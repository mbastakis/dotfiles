#!/usr/bin/env zsh
# tools.zsh - Tool initializations and shell integrations
# Note: Atuin is loaded in fzf.zsh (after fzf) so it can bind Ctrl+R

# Mise - runtime tool activation
if command -v mise &>/dev/null; then
  eval "$(mise activate zsh)"
fi

# Zoxide - smart cd
if command -v zoxide &>/dev/null; then
  # Unalias zi if it exists (conflicts with zinit)
  (( ${+aliases[zi]} )) && unalias zi
  # _ZO_FZF_OPTS is defined in fzf.zsh
  eval "$(zoxide init --cmd cd zsh)"
fi

# Direnv - per-directory environment
command -v direnv &>/dev/null && eval "$(direnv hook zsh)"

# Starship - prompt
command -v starship &>/dev/null && eval "$(starship init zsh)"

# aws-login - shell integration + agent skills
if command -v aws-login &>/dev/null; then
  eval "$(aws-login init zsh)"
  [[ ! -f ~/.config/opencode/skills/aws-login/SKILL.md ]] && aws-login skills install opencode &>/dev/null
fi
