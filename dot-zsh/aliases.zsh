# aliases.zsh - Shell aliases

# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Listing
alias l="eza --color=always --icons=always --no-user"
alias ls="eza --color=always --no-user"
alias ll="eza --long --color=always --icons=always --no-user"
alias la="eza --long --color=always --icons=always --no-user --all"
alias ld="eza --long --color=always --no-user --no-permissions --no-filesize --no-time --no-git --group-directories-first --tree"
alias lda="ld --git-ignore --all"
alias lg="eza --long --color=always --icons=always --no-user --git"

# Utilities
alias reload="source ~/.zshrc"

# Vim
alias v="nvim"
alias vi="nvim"
alias vim="nvim"

# Bat
alias cat="bat --paging=always --color=always --style=plain --line-range=1:1000 --decorations=always"

# Atuin
alias r="atuin search -i"

# Obsidian CLI
alias obs="obsidian-cli"
