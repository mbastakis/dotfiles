#!/usr/bin/env zsh
# fzf.zsh - fzf configuration and keybindings

# Catppuccin Mocha theme for fzf
export FZF_DEFAULT_OPTS=" \
--color=bg+:#313244,bg:#1E1E2E,spinner:#F5E0DC,hl:#F38BA8 \
--color=fg:#CDD6F4,header:#F38BA8,info:#CBA6F7,pointer:#F5E0DC \
--color=marker:#B4BEFE,fg+:#CDD6F4,prompt:#CBA6F7,hl+:#F38BA8 \
--color=selected-bg:#45475A \
--color=border:#6C7086,label:#CDD6F4"

# Default command for fzf (respects .gitignore)
export FZF_DEFAULT_COMMAND='fd --type f --strip-cwd-prefix --hidden --follow --exclude .git'

# CTRL-T: Paste selected files and directories
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="
  --walker-skip .git,node_modules,target
  --preview 'bat -n --color=always {}'
  --bind 'ctrl-/:change-preview-window(down|hidden|)'"

# ALT-C: Interactive zoxide (jump to any directory)
# Disabled fzf's default ALT-C in favor of zoxide interactive
export FZF_ALT_C_COMMAND=""

# CTRL-R: History search (atuin takes precedence if loaded)
# This config only applies if fzf's CTRL-R is used instead of atuin
export FZF_CTRL_R_OPTS="
  --preview 'echo {}' --preview-window up:3:hidden:wrap
  --bind 'ctrl-/:toggle-preview'
  --bind 'ctrl-y:execute-silent(echo -n {2..} | pbcopy)+abort'
  --color header:italic
  --header 'Press CTRL-Y to copy command into clipboard'"

# Initialize fzf shell integration (keybindings and completion)
# Note: We disable CTRL-R since atuin handles history search
if command -v fzf &>/dev/null; then
  eval "$(fzf --zsh)"
  # Unbind fzf's Ctrl+R to let atuin handle it
  bindkey -r '^R'
fi

# Atuin - shell history (loaded after fzf so it binds Ctrl+R)
command -v atuin &>/dev/null && eval "$(atuin init zsh)"

# Custom keybindings moved to keybindings.zsh
