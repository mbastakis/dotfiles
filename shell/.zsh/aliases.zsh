# aliases.zsh - Shell aliases

# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Listing
alias l="eza --color=always --no-user"
alias ls="eza --long --color=always --icons=always --no-user"
alias la="eza --long --color=always --icons=always --no-user --all"
alias ld="eza --long --color=always --icons=always --no-user --group-directories-first --tree"
alias lda="eza --long --color=always --icons=always --no-user --group-directories-first --tree --all"
alias lg="eza --long --color=always --icons=always --no-user --git"

# Utilities
alias reload="source ~/.zshrc"
alias brewup="brew update && brew upgrade && brew cleanup"
alias dotfiles="cd ~/.dotfiles"

# Vim
alias v="nvim"
alias vi="nvim"
alias vim="nvim"

# Bat
alias cat="bat"
