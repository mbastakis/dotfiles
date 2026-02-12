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

# Default preview: show lightweight completion description only
zstyle ':fzf-tab:complete:*:*' fzf-preview '[[ -n $desc ]] && echo $desc'

# Switch group using `<` and `>`
zstyle ':fzf-tab:*' switch-group '<' '>'

# Use default fzf colors from FZF_DEFAULT_OPTS
zstyle ':fzf-tab:*' fzf-flags \
  --border --height=80% --preview-window=right:50%:wrap

# Apply to all completions
zstyle ':fzf-tab:*' fzf-command fzf
zstyle ':fzf-tab:*' use-fzf-default-opts yes

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

# Use only prefix for query string to avoid ../ or ~/ leaking into fzf filter
# Default is (prefix input first) which includes the typed path in the query
zstyle ':fzf-tab:*' query-string prefix

# Prefer fzf-tab directly for TAB completion
(( ${+widgets[fzf-tab-complete]} )) && bindkey '^I' fzf-tab-complete
