#!/usr/bin/env zsh
# tools.zsh - Tool initializations and shell integrations
# Note: Atuin is loaded in fzf.zsh (after fzf) so it can bind Ctrl+R

# Zoxide - smart cd
if command -v zoxide &>/dev/null; then
  # Unalias zi if it exists (conflicts with zinit)
  (( ${+aliases[zi]} )) && unalias zi
  # Zoxide interactive (cdi) - inline with 5 lines instead of fullscreen
  export _ZO_FZF_OPTS="--height=~20 --layout=reverse --no-sort \
  --border=rounded --border-label=' Jump to directory ' --padding=0,1 \
  --prompt='  ' --pointer='→' --cycle --scrollbar='│' \
  --preview='eza --icons --color=always --group-directories-first --git {2..} 2>/dev/null; branch=\$(cd {2..} && git rev-parse --abbrev-ref HEAD 2>/dev/null) && w=\${FZF_PREVIEW_COLUMNS:-80} && line=\"──────────────────────────────────\" && txt=\"  \$branch\" && printf \"\n%*s\n%*s\n\" \$(((w+\${#line})/2)) \"\$line\" \$(((w+\${#txt})/2)) \"\$txt\"' \
  --preview-window=bottom,6,border-top \
  --bind='ctrl-/:toggle-preview,ctrl-d:preview-page-down,ctrl-u:preview-page-up' \
  --color=bg+:#313244,bg:#1E1E2E,spinner:#F5E0DC,hl:#F38BA8 \
  --color=fg:#CDD6F4,header:#F38BA8,info:#CBA6F7,pointer:#F5E0DC \
  --color=marker:#B4BEFE,fg+:#CDD6F4,prompt:#CBA6F7,hl+:#F38BA8 \
  --color=selected-bg:#45475A,border:#6C7086,label:#CBA6F7"
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
