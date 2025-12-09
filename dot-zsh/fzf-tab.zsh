#!/usr/bin/env zsh
# fzf-tab.zsh - fzf-tab configuration for interactive completion menu

# Disable sort when completing `git checkout`
zstyle ':completion:*:git-checkout:*' sort false

# Set descriptions format to enable group support
zstyle ':completion:*:descriptions' format '[%d]'

# Set list-colors to enable filename colorizing
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# Preview directory's content with eza when completing cd
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'

# Default preview: show description from carapace, or file/directory content
# The $desc variable contains the description provided by the completer (carapace)
zstyle ':fzf-tab:complete:*:*' fzf-preview '
  if [[ -n $desc ]]; then
    echo $desc
  elif [[ -f $realpath ]]; then
    bat --color=always --style=numbers --line-range=:500 $realpath
  elif [[ -d $realpath ]]; then
    eza -1 --color=always $realpath
  fi
'

# Switch group using `<` and `>`
zstyle ':fzf-tab:*' switch-group '<' '>'

# Use Catppuccin Mocha colors for fzf-tab with wrapped preview
zstyle ':fzf-tab:*' fzf-flags --color=bg+:#313244,bg:#1E1E2E,spinner:#F5E0DC,hl:#F38BA8 --color=fg:#CDD6F4,header:#F38BA8,info:#CBA6F7,pointer:#F5E0DC --color=marker:#B4BEFE,fg+:#CDD6F4,prompt:#CBA6F7,hl+:#F38BA8 --color=selected-bg:#45475A --border --height=80% --preview-window=right:50%:wrap

# Apply to all completions
zstyle ':fzf-tab:*' fzf-command fzf

# Use tmux popup if available
zstyle ':fzf-tab:*' fzf-pad 4

# Show preview for commands with arguments
zstyle ':fzf-tab:complete:systemctl-*:*' fzf-preview 'SYSTEMD_COLORS=1 systemctl status $word'
zstyle ':fzf-tab:complete:(-command-|-parameter-|-brace-parameter-|export|unset|expand):*' fzf-preview 'echo ${(P)word}'

# Preview for kill command
zstyle ':fzf-tab:complete:(kill|ps):argument-rest' fzf-preview '[[ $group == "[process ID]" ]] && ps --pid=$word -o cmd --no-headers -w -w'
zstyle ':fzf-tab:complete:(kill|ps):argument-rest' fzf-flags --preview-window=down:3:wrap

# Preview for git
zstyle ':fzf-tab:complete:git-(add|diff|restore):*' fzf-preview 'git diff $word | delta'
zstyle ':fzf-tab:complete:git-log:*' fzf-preview 'git log --color=always $word'
zstyle ':fzf-tab:complete:git-help:*' fzf-preview 'git help $word | bat -plman --color=always'
zstyle ':fzf-tab:complete:git-show:*' fzf-preview 'case "$group" in "commit tag") git show --color=always $word ;; *) git show --color=always $word | delta ;; esac'
zstyle ':fzf-tab:complete:git-checkout:*' fzf-preview 'case "$group" in "modified file") git diff $word | delta ;; "recent commit object name") git show --color=always $word | delta ;; *) git log --color=always $word ;; esac'

# Preview for docker - show description from completion
zstyle ':fzf-tab:complete:docker:*' fzf-preview 'echo $desc'
zstyle ':fzf-tab:complete:docker-*:*' fzf-preview 'echo $desc'

# Preview for kubectl - show description from completion
zstyle ':fzf-tab:complete:kubectl:*' fzf-preview 'echo $desc'
zstyle ':fzf-tab:complete:kubectl-*:*' fzf-preview 'echo $desc'

# Preview for environment variables
zstyle ':fzf-tab:complete:(-command-|-parameter-|-brace-parameter-|export|unset|expand):*' fzf-preview 'echo ${(P)word}'

# Continuous completion (accept and continue)
zstyle ':fzf-tab:*' continuous-trigger '/'
